import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime

# ==== Government Portal URL ====
URL = "https://vbgramgrep.dord.gov.in/VBGRAMG/dpc_sms_new.aspx?payload=I5QSfTE_qFAyGCeNWR1jIpuvxX0ydiOBH1YYxS12Ra3wYkZP1vDDoemxzhEunPYxstfyN4A8zRExvEXsv0Y21F4pm4swFk7ip8e_Luv2xfcCYGJbtpZVqHfWDDccjKuIEhIAshIKsroe9unG4SDNLoTDj4_n4sMdUneRVM7HOtOedIo5fJ7Q2HgJ8Dp-IMCUxFZF4gD26Gxw6urBH9ZmxD1otO3T61GrInTIP06rc8wHTIKRhCMwq1p5j0SXvEZfh9gnti931jkiPo8peURG71tlldtHLodHfuCIfhBnP7NwSWXQWpe_43LF5uRw7xeGnMpkoI2h2Jk8PVW49NxdEQ"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

FINAL_HEADER = [
    "SNo.", "Panchayats", "Total No. of Gram Panchayats (GPs)",
    "No. of Gram Panchayats (GPs) with Works in Progress",
    "Maximum Expected Unskilled Labour Engagement as per e-Muster Roll*",
    "No. of Ongoing Works for which Muster Rolls (MRs) have been Issued",
    "No. of Workers without e-KYC", "No. of Muster Rolls (MRs)",
    "ENGG_NAME", "Sector"
]


def fetch_html():
    print("🌐 Government वेबसाइट से डेटा लाया जा रहा है...")
    response = requests.get(URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def extract_table(html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="table")
    if table is None:
        raise Exception("⚠️ Table नहीं मिली। Website का structure बदल गया हो सकता है।")
    return table


def parse_rows(table):
    rows = []
    for tr in table.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        text_values = [c.get_text(strip=True) for c in cells]
        if any(v != "" for v in text_values):
            rows.append(text_values)
    return rows


def load_mapping():
    with open("mapping.json", "r", encoding="utf-8") as f:
        return json.load(f)


def build_final_json(rows, mapping):
    final_data = [FINAL_HEADER]

    for row in rows:
        if len(row) < 8:
            continue

        panchayat_name = row[1].strip()

        if panchayat_name in ["Panchayats", "2"]:
            continue

        sno = row[0]
        data_cols = row[1:8]

        if panchayat_name.lower() == "total":
            new_row = [sno] + data_cols + ["#N/A", "#N/A"]
        else:
            key = panchayat_name.upper()
            map_info = mapping.get(key, {"engg": "#N/A", "sector": "#N/A"})
            new_row = [sno] + data_cols + [map_info["engg"], map_info["sector"]]

        final_data.append(new_row)

    return final_data


def main():
    print("🔄 प्रक्रिया शुरू:", datetime.now())

    html = fetch_html()
    table = extract_table(html)
    rows = parse_rows(table)

    print(f"📋 कुल {len(rows)} rows मिलीं Table से")

    mapping = load_mapping()
    final_data = build_final_json(rows, mapping)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False)

    print(f"✅ सफलतापूर्वक data.json बन गई। कुल Rows: {len(final_data)}")


if __name__ == "__main__":
    main()
