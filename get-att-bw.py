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
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def append_fields(line_body, field_dict):
    """
    Given a line_body string that has the measurement and tags, append fields.

    Return the new line_body string.

    Take the list of fields from a dictionary and append them to the end
    of the line_body string.
    """
    
    for i, (key, value) in enumerate(field_dict.items()):
        if i + 1 == len(field_dict):
            # last item gets no comma at end
            # also applies if dict has length of 1
            line_body += key + "=" + str(value)
        else:
            line_body += key + "=" + str(value) + ","

    return line_body

def create_samples(values, type, sample_dict):
    """ 
    Create samples takes in a single row of values and updates a shared dictionary.
    
    Handle the case of tx and rx as separate types, but in the same dict structure.
    Operates on sample_dict{}
    """
    var_bytes = type + "_bytes"
    var_pkts = type + "_pkts"
    var_err = type + "_err"
    var_pct = type + "_pct"

    # Need to write all the numeric values as int
    # I don't love that this modifies the dict in place instead of returning
    # but it works for now
    sample_dict[var_bytes] = int(values[1])
    sample_dict[var_pkts] = int(values[2])
    sample_dict[var_err] = int(values[3])
    sample_dict[var_pct] = int(values[4])
    # print("Sample Dict Progress")
    # print(sample_dict)


def parse_html(response, sample_dict):
    """
    Given a response from requests, look for the metrics table and parse into dict.

    From the metrics table, create a dictionary that has only sample fields
    Calls create_samples
    """
    # Parsing the HTML
    soup = BeautifulSoup(response.content, "html.parser")

    for caption in soup.find_all("caption"):
        # print(caption.get_text())
        if caption.get_text() == "IP Traffic":
            table = caption.find_parent("table")
            break

    if not table:
        print("We didn't find the table we were looking for!")

    # print(table)

    # Write tx into tx and rx into rx
    for row in table.find_all("tr"):
        columns = row.find_all("td")
        # The th row is an empty list because it doesn't have tds, so check if columns is present
        if columns:
            # Make a new list by grabbing the text only and ditching whitespace and markup
            values = [cell.text.strip() for cell in columns]

            # Pass along the row type in [0] to create_samples
            if values[0] == "Transmit":
                # print("This is the transmit row")
                create_samples(values, "tx", sample_dict)
            elif values[0] == "Receive":
                # print("This is the receive row")
                create_samples(values, "rx", sample_dict)


def main():
    # Read in settings from TOML file
    # Set .gitignore for config.toml. See config-example.toml

    config = toml.load("config.toml")
    # print(config)

    router_ip = config["router"]["ip"]
    router_host = config["router"]["host"]
    router_region = config["router"]["region"]

    influx_bucket = config["influx2"]["bucket"]
    influx_measurement = config["influx2"]["measurement"]

    router_bw_url = "http://" + router_ip + "/xslt?PAGE=C_1_0"

    # print(f"Router IP: {router_ip} results in URL: {router_bw_url}")

    # Make the request
    # TODO - add Retry
    response = requests.get(router_bw_url)

    # Print the status code. Check this later
    # print(response)

    # Process the response and update sample_dict{}
    sample_dict = {}
    parse_html(response, sample_dict)

    """
    Now we have a sample_dict{} that has everything we want. Have to pass this to influxdb
    Add measurement names and tags.
    And a destination IP, pass(v 1.8, tokens if newer), and db name
    """

    # print("Sample Dictionary")
    # print(sample_dict)

    measurement = {}
    # Simple measurement name - usually "net"
    measurement["measurement"] = influx_measurement
    # Simple tags for host and region. Could make this more flexible later if needed.
    measurement["tags"] = { "host": router_host, "region": router_region }
    # Dictionary of fields and their values
    measurement["fields"] = sample_dict

    # Now build first part of line protocol from the dictionary.

    line_body = measurement["measurement"] + \
                ",host=" + measurement["tags"]["host"] + \
                ",region=" + measurement["tags"]["region"] + \
                " "
                
    # print("This is the first half of line format version.")
    # print(line_body)

    # print("Calling append_fields")
    line_body = append_fields(line_body, sample_dict)
    # print(line_body)

    # 1.8 client
    # client = InfluxDBClient(influx_ip, influx_port, influx_user, influx_pass, influx_db, ssl=True, timeout=1, retries=3)

    # 1.8 client
    # Let's write line protocol instead.
    # client.write_points(line_body, protocol="line")

    # setup urllib retries
    #retries = urllib3.Retry(connect=3, read=2, redirect=3)
    # how do I make that work with from_config_file?

    # 2.0 client from example
    with InfluxDBClient.from_config_file("config.toml") as client:
        with client.write_api(write_options=SYNCHRONOUS) as writer:
            writer.write(bucket=influx_bucket, record=line_body)


if __name__ == "__main__":
    main()
