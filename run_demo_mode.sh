#!/bin/bash
echo "🚀 Waiting for jobs... (Press Ctrl+C to stop)"

# Track the last processed job to clean up before next one
LAST_JOB_ID=""

while true; do
    JOB_JSON=$(aws dynamodb scan \
        --table-name landuse-rondonia-analysis-jobs-dev \
        --filter-expression "#s = :q" \
        --expression-attribute-names '{"#s": "status"}' \
        --expression-attribute-values '{":q": {"S": "QUEUED"}}' \
        --region us-west-2 \
        --query "Items[0]" \
        --output json 2>/dev/null)

    JOB_ID=$(echo "$JOB_JSON" | jq -r '.job_id.S // empty' 2>/dev/null)
    CREATED_AT=$(echo "$JOB_JSON" | jq -r '.created_at.N // empty' 2>/dev/null)

    if [[ -n "$JOB_ID" && "$JOB_ID" != "null" && -n "$CREATED_AT" && "$CREATED_AT" != "null" ]]; then
        echo ""
        echo "============================================"
        echo "⚡ Found Job: $JOB_ID"
        echo "   Timestamp: $CREATED_AT"
        echo "============================================"

        # --- CLEANUP PREVIOUS JOB ---
        if [[ -n "$LAST_JOB_ID" && "$LAST_JOB_ID" != "$JOB_ID" ]]; then
            echo "🧹 Cleaning previous job data from S3..."
            aws s3 rm "s3://landuse-rondonia-data-dev/results/$LAST_JOB_ID/" --recursive --region us-west-2 2>/dev/null
            echo "   Deleted s3://landuse-rondonia-data-dev/results/$LAST_JOB_ID/"
        fi

        # Clean local temp files
        rm -rf /tmp/landuse-processing/*

        # Lock to PROCESSING
        aws dynamodb update-item \
            --table-name landuse-rondonia-analysis-jobs-dev \
            --key "{\"job_id\": {\"S\": \"$JOB_ID\"}, \"created_at\": {\"N\": \"$CREATED_AT\"}}" \
            --update-expression "SET #s = :p, progress = :prog" \
            --expression-attribute-names '{"#s": "status"}' \
            --expression-attribute-values '{":p": {"S": "PROCESSING"}, ":prog": {"N": "10"}}' \
            --region us-west-2 2>/dev/null

        echo "🔒 Status locked to PROCESSING"

        # Run processor
        echo "🔄 Running ec2_process_job.py..."
        python3.11 ~/ec2_process_job.py "$JOB_ID" 2>&1
        PROCESS_EXIT=$?

        if [ $PROCESS_EXIT -ne 0 ]; then
            echo "❌ ec2_process_job.py failed with exit code $PROCESS_EXIT"
            aws dynamodb update-item \
                --table-name landuse-rondonia-analysis-jobs-dev \
                --key "{\"job_id\": {\"S\": \"$JOB_ID\"}, \"created_at\": {\"N\": \"$CREATED_AT\"}}" \
                --update-expression "SET #s = :f, error_message = :e" \
                --expression-attribute-names '{"#s": "status"}' \
                --expression-attribute-values "{\":f\": {\"S\": \"FAILED\"}, \":e\": {\"S\": \"Process exited with code $PROCESS_EXIT\"}}" \
                --region us-west-2 2>/dev/null
            sleep 2
            continue
        fi

        # Run encroachment detection if files exist
        DEFOR_FILE="/tmp/landuse-processing/$JOB_ID/deforestation.tif"
        URBAN_FILE="/tmp/landuse-processing/$JOB_ID/urban_expansion.tif"

        if [ -f "$DEFOR_FILE" ] && [ -f "$URBAN_FILE" ]; then
            echo "🔄 Running ec2_encroachment_detection.py..."
            python3.11 ~/ec2_encroachment_detection.py "$JOB_ID" "$DEFOR_FILE" "$URBAN_FILE" 2>&1 || true
        fi

        # Safety net — ensure COMPLETED
        aws dynamodb update-item \
            --table-name landuse-rondonia-analysis-jobs-dev \
            --key "{\"job_id\": {\"S\": \"$JOB_ID\"}, \"created_at\": {\"N\": \"$CREATED_AT\"}}" \
            --update-expression "SET #s = :c, progress = :prog" \
            --expression-attribute-names '{"#s": "status"}' \
            --expression-attribute-values '{":c": {"S": "COMPLETED"}, ":prog": {"N": "100"}}' \
            --region us-west-2 2>/dev/null

        LAST_JOB_ID="$JOB_ID"
        echo "✅ Job $JOB_ID DONE!"
        echo "============================================"
	echo "👀 Watching for next job..."
    else
        # Print a dot every 60 seconds to show the loop is alive
        COUNTER=${COUNTER:-0}
        COUNTER=$((COUNTER + 1))
        if [ $((COUNTER % 12)) -eq 0 ]; then
            echo "⏳ Still watching... ($(date '+%H:%M:%S'))"
        fi
    fi

    sleep 5
done
