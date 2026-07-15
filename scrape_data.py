import json
from playwright.sync_api import sync_playwright
from datetime import datetime

URL = "https://vbgramgrep.dord.gov.in/VBGRAMG/dpc_sms_new.aspx?payload=I5QSfTE_qFAyGCeNWR1jIpuvxX0ydiOBH1YYxS12Ra3wYkZP1vDDoemxzhEunPYxstfyN4A8zRExvEXsv0Y21F4pm4swFk7ip8e_Luv2xfcCYGJbtpZVqHfWDDccjKuIEhIAshIKsroe9unG4SDNLoTDj4_n4sMdUneRVM7HOtOedIoSfJ7Q2HgJ8Dp-IMCUxFZF4gD26Gxw6urBH9ZmxD1otO3T61GrInTIP06rc8wHTIKRhCMwq1p5j0SXvEZfh9gnti931jkiPo8peURG71tlldtHLodHfuCIfhBnP7NwSWXQWpe_43LF5uRw7xeGnMpkoI2h2Jk8PVW49NxdEQ"

FINAL_HEADER = [
    "SNo.", "Panchayats", "Total No. of Gram Panchayats (GPs)",
    "No. of Gram Panchayats (GPs) with Works in Progress",
    "Maximum Expected Unskilled Labour Engagement as per e-Muster Roll*",
    "No. of Ongoing Works for which Muster Rolls (MRs) have been Issued",
    "No. of Workers without e-KYC", "No. of Muster Rolls (MRs)",
    "ENGG_NAME", "Sector"
]


def fetch_table_data():
    rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("🌐 पेज खोला जा रहा है...")
        response = page.goto(URL, wait_until="networkidle", timeout=60000)
        print("Status Code:", response.status if response else "N/A")

        try:
            page.wait_for_selector("table.table", timeout=30000)
        except Exception:
            print("⚠️ Table selector 30 sec में नहीं मिला, फिर भी आगे बढ़ रहे हैं...")

        # Debug: पेज का Title और थोड़ा HTML print करना
        print("पेज का Title:", page.title())

        table_locator = page.locator("table.table").first
        count = table_locator.count()
        print("टेबल मिली क्या (count):", count)

        if count == 0:
            # पूरा HTML देखकर debug करना
            content = page.content()
            print("---- पेज के HTML का पहला 1000 characters ----")
            print(content[:1000])
            browser.close()
            raise Exception("⚠️ Table नहीं मिली। ऊपर HTML देखें।")

        row_count = table_locator.locator("tr").count()
        print(f"📋 Table में कुल {row_count} tr मिले")

        for i in range(row_count):
            tr = table_locator.locator("tr").nth(i)
            cell_count = tr.locator("td, th").count()
            row_data = []
            for j in range(cell_count):
                text = tr.locator("td, th").nth(j).inner_text().strip()
                row_data.append(text)
            if any(v != "" for v in row_data):
                rows.append(row_data)

        browser.close()
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

    rows = fetch_table_data()
    print(f"✅ कुल {len(rows)} rows निकाली गईं")

    if len(rows) == 0:
        raise Exception("❌ कोई भी row नहीं मिली।")

    mapping = load_mapping()
    final_data = build_final_json(rows, mapping)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False)

    print(f"✅ सफलतापूर्वक data.json बन गई। कुल Rows: {len(final_data)}")


if __name__ == "__main__":
    main()
