[DefaultOutputDestinationSettings = [DestinationDefinition = [Kind = "Reference", QueryName = "DefaultDestination", IsNewTarget = true], UpdateMethod = [Kind = "Replace"], DestinationTypeSettings = [Kind = "Table"]], StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[BindToDefaultDestination = true]
shared openaq_measurements_raw = let
    api_key = "a29ccffdf83bb2507716d7f2d1c6172a243e8813c79a2ebdc0b62e38b6cf4c01",
    base_url = "https://api.openaq.org",
    
    locations_response = Json.Document(
        Web.Contents(base_url, [
            RelativePath = "/v3/locations",
            Query = [
                coordinates = "40.7128,-74.0060",
                radius = "25000",
                limit = "100"
            ],
            Headers = [#"X-API-Key" = api_key]
        ])
    ),
    locations_results = locations_response[results],
    
    LocationsTable = Table.FromList(locations_results, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    ExpandedLocations = Table.ExpandRecordColumn(LocationsTable, "Column1",
        {"id", "name", "datetimeFirst", "datetimeLast", "sensors"},
        {"location_id", "location_name", "datetimeFirst", "datetimeLast", "sensors"}),
    
    ExpandedFirst = Table.ExpandRecordColumn(ExpandedLocations, "datetimeFirst",
        {"utc"}, {"first_date"}),
    ExpandedLast = Table.ExpandRecordColumn(ExpandedFirst, "datetimeLast",
        {"utc"}, {"last_date"}),
    Active2024 = Table.SelectRows(ExpandedLast, each 
        [first_date] <= "2024-12-31" and [last_date] >= "2024-01-01"),
    
    ExpandedSensorsList = Table.ExpandListColumn(Active2024, "sensors"),
    ExpandedSensorsRecord = Table.ExpandRecordColumn(ExpandedSensorsList, "sensors",
        {"id", "parameter"},
        {"sensor_id", "parameter"}),
    ExpandedParameter = Table.ExpandRecordColumn(ExpandedSensorsRecord, "parameter",
        {"name", "units"},
        {"parameter_name", "parameter_units"}),
    
    FilteredSensors = Table.SelectRows(ExpandedParameter, each 
        [parameter_name] = "pm25" or [parameter_name] = "no2" or [parameter_name] = "o3"),
    
    SensorIds = List.Distinct(FilteredSensors[sensor_id]),
    
    GetSensorDays = (sensor_id as number) =>
        let
            result = try Json.Document(
                Web.Contents(base_url, [
                    RelativePath = "/v3/sensors/" & Number.ToText(sensor_id) & "/days",
                    Query = [
                        date_from = "2024-01-01",
                        date_to = "2024-12-31",
                        limit = "400"
                    ],
                    Headers = [#"X-API-Key" = api_key]
                ])
            ),
            results_list = if result[HasError] then {} else result[Value][results],
            WithSensorId = List.Transform(results_list, each Record.AddField(_, "sensor_id", sensor_id))
        in
            WithSensorId,
    
    AllData = List.Combine(List.Transform(SensorIds, each GetSensorDays(_))),
    
    AsTable = Table.FromList(AllData, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    Expanded = Table.ExpandRecordColumn(AsTable, "Column1",
        {"sensor_id", "value", "parameter", "period", "coordinates"},
        {"sensor_id", "value", "parameter", "period", "coordinates"}),
    
    ExpandedParam2 = Table.ExpandRecordColumn(Expanded, "parameter",
        {"name", "units"},
        {"parameter_name", "parameter_units"}),
    
    ExpandedPeriod = Table.ExpandRecordColumn(ExpandedParam2, "period",
        {"datetimeFrom"}, {"period_from"}),
    ExpandedDate = Table.ExpandRecordColumn(ExpandedPeriod, "period_from",
        {"local"}, {"measurement_date"}),
    
    ExpandedCoords = Table.ExpandRecordColumn(ExpandedDate, "coordinates",
        {"latitude", "longitude"},
        {"lat", "lon"}),
    
    TypedTable = Table.TransformColumnTypes(ExpandedCoords, {
        {"sensor_id", Int64.Type},
        {"value", type number},
        {"parameter_name", type text},
        {"parameter_units", type text},
        {"measurement_date", type text},
        {"lat", type number},
        {"lon", type number}
    })
in
    TypedTable;
shared DefaultDestination = Lakehouse.Contents([EnableFolding = false]){[workspaceId = "b200716b-df87-4d85-855d-bba1dc5bec4b"]}[Data]{[lakehouseId = "a20c4fee-6f4c-4826-bb20-9f7c6dc1a057"]}[Data];
