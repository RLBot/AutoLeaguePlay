import pickle
from dataclasses import dataclass
from typing import List

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from autoleagueplay.ladder import Ladder
from autoleagueplay.paths import PackageFiles


@dataclass
class SeasonSheet:
    season: int
    sheet_id: str
    sheet_name: str
    initial_ladder_col: int  # E.g. column D is 4
    rank_one_row: int
    ladder_length: int
    ladder_spacing: int  # Number of columns between each ladder


# The sheet info for each season
SEASONS = [
    SeasonSheet(
        0, "1XULvW97g46EdrYRuhiHBfARDkviULYjRO5dA8sMmxkY", "Off Season 0", 4, 4, 50, 1
    ),
    SeasonSheet(
        1, "1XULvW97g46EdrYRuhiHBfARDkviULYjRO5dA8sMmxkY", "Season 1", 4, 4, 60, 2
    ),
]

# If modifying these scopes, delete the file 'cred/sheets-api-token.pickle'
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def fetch_ladder_from_sheets(season: int, week_num: int) -> Ladder:
    bots = fetch_bots_from_sheets(season, week_num)
    return Ladder(bots)


def fetch_bots_from_sheets(season: int, week_num: int) -> List[str]:
    assert 0 <= season < len(SEASONS), "Invalid or unknown season number"
    season_sheet = SEASONS[season]
    range = get_ladder_range(season_sheet, week_num)
    values = get_values_from_sheet(
        get_credentials(), season_sheet.sheet_id, range, season_sheet.sheet_name
    )
    return [row[0] for row in values]


def get_ladder_range(season_sheet: SeasonSheet, week_num: int) -> str:
    col = get_col_name(
        season_sheet.initial_ladder_col + week_num * (1 + season_sheet.ladder_spacing)
    )
    return f"{col}{season_sheet.rank_one_row}:{col}{season_sheet.rank_one_row + season_sheet.ladder_length}"


def get_col_name(col_num: int) -> str:
    """
    Transforms a column number to its column name. I.e. 1 => A, 2 => B, 27 => AA, 14558 => UMX
    :param col_num:
    :return: the name of the column
    """
    numeric = (col_num - 1) % 26
    letter = chr(65 + numeric)
    remaining_index = (col_num - 1) // 26
    if remaining_index > 0:
        return get_col_name(remaining_index - 1) + letter
    else:
        return letter


def get_credentials():
    creds = None
    # The file 'cred/sheets-api-token.pickle' stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if PackageFiles.sheets_token.exists():
        with open(PackageFiles.sheets_token, "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if PackageFiles.credentials.exists():
                flow = InstalledAppFlow.from_client_secrets_file(
                    PackageFiles.credentials, SHEETS_SCOPES
                )
                creds = flow.run_local_server(port=0)
            else:
                raise ValueError(
                    f"""ERROR: Cannot use Google Sheet API due to missing credentials.
                    Go to \'https://developers.google.com/sheets/api/quickstart/python\'.
                    Click the \'Enable the Google Sheets API\' button, accept, and download the \'credentials.json\'.
                    Put the \'credentials.json\' in the directory \'{PackageFiles.credentials.parent.absolute()}\' and try again.
                    Next time you run the script a browser will open, where Google asks you if this script can get permission.
                    Afterwards everything should work.
                    """
                )
        # Save the credentials for the next run
        with open(PackageFiles.sheets_token, "wb") as token:
            pickle.dump(creds, token)
    return creds


def get_values_from_sheet(
    creds, spreadsheet_id: str, range: str, sheet_name: str
) -> List[List[str]]:
    """
    Uses the Google Sheets API v4 to fetch the values from a spreadsheet.
    :param creds: credentials
    :param spreadsheet_id: the id of the spreadsheet. Can be found in the link. E.g.: '1u7iWUg0LA4wWaTMoDuBbBuA4de_fdL_kSxLyIQruvkg'
    :param range: the range to fetch, e.g.: 'D4:D48'
    :param sheet_name: the sheet name, e.g.: 'Ark1'
    :return: a list of rows that are lists of strings.
    """

    range_name = str(sheet_name) + "!" + str(range)

    service = build("sheets", "v4", credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = (
        sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    )
    return result.get("values", [])


if __name__ == "__main__":
    # As test, fetch and print the initial ladder
    bots = fetch_bots_from_sheets(1, 0)
    print(bots)
