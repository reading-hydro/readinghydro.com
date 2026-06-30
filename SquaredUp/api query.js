// start date , end date

{{const startDate = new Date(timeframe.start);
startDate.getUTCFullYear() + (startDate.getUTCMonth() + 1).toString().padStart(2, '0') + startDate.getUTCDate().toString().padStart(2, '0')}}/

{{const endDate = new Date(timeframe.end);
endDate.getUTCFullYear() + (endDate.getUTCMonth() + 1).toString().padStart(2, '0') + endDate.getUTCDate().toString().padStart(2, '0')}}

{{new Date(timeframe.start).toISOString().split('T')[0]}}
