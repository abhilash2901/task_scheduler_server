from dateutil import tz

def get_distance_n_duration(source,dest,departure_time=None):
    # importing required libraries
    import requests, json

    # enter your api key here
    # api_key = 'AIzaSyDBt3nqcRiisQA8ITzYKMMWrL2PF3BGhXk'
    api_key = 'AIzaSyDYicvTBfltvPF3Ms8-UciPMCNDcWl9xlY'

    # Take source as input
    # source = "kazhakoottam"

    # Take destination as input
    # dest = "neyyattinkara"

    # url variable store url

    # Get method of requests module
    # return response object

    from datetime import datetime
    now = datetime.now()
    # importing googlemaps module
    import googlemaps
    if not departure_time:
        departure_time = now
    # Requires API key
    gmaps = googlemaps.Client(key=api_key)

    # Requires cities name
    r = gmaps.distance_matrix(source,dest,departure_time=departure_time)['rows'][0]['elements'][0]['duration_in_traffic']['text']

    # Printing the result


    return r

    # r = requests.get(
    #     "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=%s&destinations=%s&key=%s" % (
    #         source, dest, api_key))
    #
    #
    #
    # # json method of response object
    # # return json format result
    # x = r.json()
    #
    # # bydefault driving mode considered
    #
    # # print the vale of x
    # return x
