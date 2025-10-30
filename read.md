 metrics:
      query: |
        SELECT 
          total_records,
          failed_records,
          success_records,
          processing_date
        FROM process_summary
        WHERE process_id = :process_id
        AND run_date = :run_date
      
      parameters:
        process_id: "CLAIMS_PROC_001"
        run_date: "{current_date}"
      
      fields:
        - column: "total_records"
          label: "Total Claims Records"
          format: "number"
        - column: "failed_records"
          label: "Failed Records"
          format: "number"
          highlight_if: "> 0"  # Optional: highlight if value > 0
        - column: "success_records"
          label: "Successfully Processed"
          format: "number"
        - column: "processing_date"
          label: "Processing Date"
          format: "date"
