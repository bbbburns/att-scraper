"""
Ideal JSON Data Structure for Measurement
json_body = [
{
    "measurement": "net",
    "tags": {
        "host": "router",
        "region": "livingstone"
    },
    "time": "2023-09-24T00:00:00Z",
    "fields": {
        "tx_bytes": "X",
        "tx_pkts": "X",
        "tx_err": "X",
        "tx_err_pct": "X",
        "rx_bytes": "X",
        "rx_pkts": "X",
        "rx_err": "X",
        "rx_err_pct": "X"
    }
}
]
"""
import requests
from bs4 import BeautifulSoup

sample_dict = {}

def create_samples(values, type):
    """ 
    Handle the case of tx and rx as separate types, but in the same structure.
    """
    var_bytes = type + "_bytes"
    var_pkts = type + "_pkts"
    var_err = type + "_err"
    var_pct = type + "_pct"

    sample_dict[var_bytes] = values[1]
    sample_dict[var_pkts] = values[2]
    sample_dict[var_err] = values[3]
    sample_dict[var_pct] = values[4]
    #print("Sample Dict Progress")
    #print(sample_dict)


r = requests.get("http://192.168.1.254/xslt?PAGE=C_1_0")

# Print the status code. Check this later
# print(r)

# Parsing the HTML
soup = BeautifulSoup(r.content, "html.parser")

for caption in soup.find_all("caption"):
    # print(caption.get_text())
    if caption.get_text() == "IP Traffic":
        table = caption.find_parent("table")
        break

if not table:
    print("We didn't find the table we were looking for!")

# print(table)

"""
 The dumbest way to do this would be to loop through the first data row 
 and store the fixed indices as the tx values, then loop through the second
 row and store the indices as the rx values.

 I'd be happier if this did something smart and read the headers and took the
 correct action based on the header name. Oh well.
"""

for row in table.find_all("tr"):
    columns = row.find_all("td")
    # The th row is an empty list because it doesn't have tds, so check if columns is present
    if columns:
        # print("Printing this column")
        # print(columns)
        # print(columns[0].text.strip())
        # print(columns[1].text.strip())
        # print(columns[2].text.strip())
        # print(columns[3].text.strip())
        # print(columns[4].text.strip())

        # Make a new list by grabbing the text only and ditching whitespace and markup
        values = [cell.text.strip() for cell in columns]

        # Pass along the row type
        if values[0] == "Transmit":
            # print("This is the transmit row")
            create_samples(values, "tx")
        elif values[0] == "Receive":
            # print("This is the receive row")
            create_samples(values, "rx")

"""
Now we have a sample_dict that has everything we want. Have to pass this to influxdb
Probably needs tags and devices names or something like that
And a destination IP, pass(v 1.8, tokens if newer), cert, and db name?
"""

print("Sample Dictionary")
print(sample_dict)