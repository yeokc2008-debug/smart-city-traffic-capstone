// Create a Text parameter CsvPath with the full path to data/Metro_Interstate_Traffic_Volume.csv.
// Create a blank query named TrafficRaw and paste this expression in Advanced Editor.
let
 Source=Csv.Document(File.Contents(CsvPath),[Delimiter=",",Columns=9,Encoding=65001,QuoteStyle=QuoteStyle.Csv]),
 Headers=Table.PromoteHeaders(Source,[PromoteAllScalars=true]),
 Typed=Table.TransformColumnTypes(Headers,{{"holiday",type text},{"temp",type number},{"rain_1h",type number},{"snow_1h",type number},{"clouds_all",Int64.Type},{"weather_main",type text},{"weather_description",type text},{"date_time",type datetime},{"traffic_volume",Int64.Type}},"en-US")
in Typed
