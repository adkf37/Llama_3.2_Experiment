# Homicides Data Schema (Homicides_2001_to_present.csv)

This dataset contains records of homicides in Chicago, Illinois. Each row represents a single incident.

Key Columns:
- **ID**: Unique identifier for the record.
- **Case Number**: The case number associated with the incident.
- **Date**: Date and time of the incident.
- **Block**: The block address where the incident occurred (address partially redacted for privacy).
- **IUCR**: Illinois Uniform Crime Reporting code. This code specifies the type of crime.
- **Primary Type**: The primary description of the IUCR code (e.g., HOMICIDE, THEFT).
- **Description**: A more specific description of the crime.
- **Location Description**: Description of the location where the incident occurred (e.g., STREET, APARTMENT).
- **Arrest**: Boolean (true/false) indicating if an arrest was made.
- **Domestic**: Boolean (true/false) indicating if the incident was domestic-related.
- **Beat**: The police beat where the incident occurred.
- **District**: The police district where the incident occurred.
- **Ward**: The city ward where the incident occurred.
- **Community Area**: The community area number.
- **FBI Code**: FBI crime code.
- **X Coordinate**: X-coordinate of the location (projected).
- **Y Coordinate**: Y-coordinate of the location (projected).
- **Year**: Year the incident occurred.
- **Updated On**: Date and time the record was last updated.
- **Latitude**: Latitude of the location.
- **Longitude**: Longitude of the location.
- **Location**: Combined latitude and longitude.

When querying this data, refer to these column names to understand the meaning of the values in each row. For example, a query about "arrests in 2023" would relate to the 'Arrest' and 'Year' columns.