[DefaultOutputDestinationSettings = [DestinationDefinition = [Kind = "Reference", QueryName = "DefaultDestination", IsNewTarget = true], UpdateMethod = [Kind = "Replace"], DestinationTypeSettings = [Kind = "Table"]], StagingDefinition = [Kind = "FastCopy"]]
section Section1;
shared DefaultDestination = Lakehouse.Contents([EnableFolding = false]){[workspaceId = "b200716b-df87-4d85-855d-bba1dc5bec4b"]}[Data]{[lakehouseId = "a20c4fee-6f4c-4826-bb20-9f7c6dc1a057"]}[Data];
[BindToDefaultDestination = true]
shared worldbank_gdp_raw = let
    base_url = "https://api.worldbank.org",
    
    response = Json.Document(
        Web.Contents(base_url, [
            RelativePath = "/v2/country/USA/indicator/NY.GDP.MKTP.CD",
            Query = [
                format = "json",
                per_page = "200"
            ]
        ])
    ),
    
    data_array = response{1},
    
    AsTable = Table.FromList(data_array, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    
    Expanded = Table.ExpandRecordColumn(AsTable, "Column1",
        {"indicator", "country", "countryiso3code", "date", "value"},
        {"indicator", "country", "country_code", "year", "gdp_value"}),
    
    ExpandedIndicator = Table.ExpandRecordColumn(Expanded, "indicator",
        {"id", "value"},
        {"indicator_id", "indicator_name"}),
    
    ExpandedCountry = Table.ExpandRecordColumn(ExpandedIndicator, "country",
        {"value"},
        {"country_name"}),
    
    FilteredNonNull = Table.SelectRows(ExpandedCountry, each [gdp_value] <> null),
    
    TypedTable = Table.TransformColumnTypes(FilteredNonNull, {
        {"indicator_id", type text},
        {"indicator_name", type text},
        {"country_code", type text},
        {"country_name", type text},
        {"year", Int64.Type},
        {"gdp_value", type number}
    })
in
    TypedTable;
