"""
Pull the data in based on some stackoverflow beautifulsoup table examples

Output the data to Influx 1.8 https://github.com/influxdata/influxdb-python

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
        "tx_bytes": X,
        "tx_pkts": X,
        "tx_err": X,
        "tx_err_pct": X,
        "rx_bytes": X,
        "rx_pkts": X,
        "rx_err": X,
        "rx_err_pct": X
    }
}
]

Ideal line protocol for measurement. Line breaks added for clarity.

net,host=router,region=livingstone tx_bytes=3713275163,tx_pkts=56434892,
                                   tx_err=0,tx_pct=0,rx_bytes=4909425,
                                   rx_pkts109068990,rx_err=0,rx_pct=0
"""
import toml
import requests
from bs4 import BeautifulSoup
import json
from influxdb import InfluxDBClient
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sample_dict = {}
measurement = {}

def create_samples(values, type):
    """ 
    Create samples takes in a single row of values and updates a shared dictionary.
    Handle the case of tx and rx as separate types, but in the same dict structure.
    """
    var_bytes = type + "_bytes"
    var_pkts = type + "_pkts"
    var_err = type + "_err"
    var_pct = type + "_pct"

    # Need to write all the numeric values as int
    sample_dict[var_bytes] = int(values[1])
    sample_dict[var_pkts] = int(values[2])
    sample_dict[var_err] = int(values[3])
    sample_dict[var_pct] = int(values[4])
    # print("Sample Dict Progress")
    # print(sample_dict)


def main():
    # Read in settings from TOML file
    # Set .gitignore for config.toml. See config-example.toml

    config = toml.load("config.toml")
    # print(config)

    router_dict = config["router"]
    influx_dict = config["influxdb"]

    # print(router_dict)
    # print(influx_dict)

    router_ip = router_dict["ip"]
    router_host = router_dict["host"]
    router_region = router_dict["region"]

    influx_ip = influx_dict["ip"]
    influx_port = influx_dict["port"]
    influx_db = influx_dict["db"]
    influx_user = influx_dict["user"]
    influx_pass = influx_dict["pass"]
    influx_measurement = influx_dict["measurement"]

    router_bw_url = "http://" + router_ip + "/xslt?PAGE=C_1_0"

    # print(f"Router IP: {router_ip} results in URL: {router_bw_url}")

    # Make the request
    r = requests.get(router_bw_url)

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

    # print("Sample Dictionary")
    # print(sample_dict)

    measurement["measurement"] = influx_measurement
    measurement["tags"] = { "host": router_host, "region": router_region }
    measurement["fields"] = sample_dict

    #fmt_msmt = json.dumps(measurement)
    # print("This is the measurement")
    # print(measurement)
    # print(json.dumps(measurement))

    """
    json_body = [
        {
            "measurement": "net",
            "tags": {
                "host": "router",
                "region": "livingstone"
            },
            "fields": {
                "tx_bytes": 3713275163,
                "tx_pkts": 56434892,
                "tx_err": 0,
                "tx_pct": 0,
                "rx_bytes": 4909425,
                "rx_pkts": 109068990,
                "rx_err": 0,
                "rx_pct": 0
            }
        }
    ]
    """

    #body = []
    #body.append(measurement)
    
    #print("This is the Python body")
    #print(body)

    #json_body = json.dumps(body)
    #print("This is the json_body")
    #print(json_body)


    # Now build line protocol.
    # I don't like this at all.

    line_body = measurement["measurement"] + \
                ",host=" + measurement["tags"]["host"] + \
                ",region=" + measurement["tags"]["region"] + \
                " " + \
                "tx_bytes=" + str(measurement["fields"]["tx_bytes"]) + \
                ",tx_pkts=" + str(measurement["fields"]["tx_pkts"]) + \
                ",tx_err=" + str(measurement["fields"]["tx_err"]) + \
                ",tx_pct=" + str(measurement["fields"]["tx_pct"]) + \
                ",rx_bytes=" + str(measurement["fields"]["rx_bytes"]) + \
                ",rx_pkts=" + str(measurement["fields"]["rx_pkts"]) + \
                ",rx_err=" + str(measurement["fields"]["rx_err"]) + \
                ",rx_pct=" + str(measurement["fields"]["rx_pct"])

    # print("This is the line format version.")
    # print(line_body)
    #body.append(line_body)
    #print("This is the full body, an array of one.")
    #print(body)

    client = InfluxDBClient(influx_ip, influx_port, influx_user, influx_pass, influx_db, ssl=True)

    # This always fails because it can't convert my json body for some reason.
    # I don't see ANY difference between my json body built by hand vs the one
    # in code.
    # Maybe it's some unicode or encoding problem?
    # client.write_points(json_body)

    # Let's write line protocol instead.
    client.write_points(line_body, protocol="line")


if __name__ == "__main__":
    main()
