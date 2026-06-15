# file: dummy_customer_api.py
from flask import Flask, request, jsonify
import random

app = Flask(__name__)

# simulate messy unstructured text responses
ORDERS = [
    "Order 1001: Buyer=John Davis, Location=Columbus, OH, Total=$742.10, Items: laptop, hdmi cable",
    "Order 1002: Buyer=Sarah Liu, Location=Austin, TX, Total=$156.55, Items: headphones",
    "Order 1003: Buyer=Mike Turner, Location=Cleveland, OH, Total=$1299.99, Items: gaming pc, mouse",
    "Order 1004: Buyer=Rachel Kim, Location=Seattle, WA, Total=$89.50, Items: coffee maker",
    "Order 1005: Buyer=Chris Myers, Location=Cincinnati, OH, Total=$512.00, Items: monitor, desk lamp",
    "Order 1006: Buyer=Amanda Foster, Location=Denver, CO, Total=$234.75, Items: keyboard, mouse pad",
    "Order 1007: Buyer=Daniel Park, Location=Portland, OR, Total=$879.00, Items: tablet, stylus",
    "Order 1008: Buyer=Lisa Chen, Location=Chicago, IL, Total=$45.99, Items: usb hub",
    "Order 1009: Buyer=Brian Thompson, Location=Phoenix, AZ, Total=$1450.00, Items: standing desk",
    "Order 1010: Buyer=Emily Watson, Location=Miami, FL, Total=$320.50, Items: webcam, ring light",
    "Order 1011: Buyer=Kevin O'Brien, Location=Boston, MA, Total=$67.25, Items: ethernet cable, surge protector",
    "Order 1012: Buyer=Megan Hall, Location=Nashville, TN, Total=$999.99, Items: noise cancelling headphones",
    "Order 1013: Buyer=Jason Rivera, Location=San Diego, CA, Total=$185.40, Items: external hard drive",
    "Order 1014: Buyer=Stephanie Moore, Location=Atlanta, GA, Total=$2100.00, Items: ultrawide monitor, monitor arm",
    "Order 1015: Buyer=Tyler Scott, Location=Minneapolis, MN, Total=$54.00, Items: mousepad xl",
    "Order 1016: Buyer=Natalie Adams, Location=Las Vegas, NV, Total=$710.80, Items: graphics card",
    "Order 1017: Buyer=Marcus Johnson, Location=Detroit, MI, Total=$389.99, Items: mechanical keyboard, wrist rest",
    "Order 1018: Buyer=Olivia Martinez, Location=Orlando, FL, Total=$129.00, Items: bluetooth speaker",
    "Order 1019: Buyer=Ryan Cooper, Location=Kansas City, MO, Total=$3200.00, Items: workstation pc",
    "Order 1020: Buyer=Hannah Lee, Location=Salt Lake City, UT, Total=$76.50, Items: laptop stand, cable organizer",
    "Order 1021: Buyer=Derek Williams, Location=Philadelphia, PA, Total=$550.00, Items: smart display",
    "Order 1022: Buyer=Chloe Brown, Location=San Jose, CA, Total=$198.75, Items: drawing tablet",
    "Order 1023: Buyer=Aaron Nelson, Location=Charlotte, NC, Total=$410.00, Items: docking station",
    "Order 1024: Buyer=Grace Patel, Location=Houston, TX, Total=$88.99, Items: screen cleaner kit, privacy screen",
    "Order 1025: Buyer=Ian Robinson, Location=Indianapolis, IN, Total=$1750.00, Items: server rack, patch panel",
    "Order 1026: Buyer=Victoria Clark, Location=Memphis, TN, Total=$245.60, Items: portable ssd",
    "Order 1027: Buyer=Ethan Lewis, Location=Louisville, KY, Total=$60.00, Items: hdmi splitter",
    "Order 1028: Buyer=Sophia Walker, Location=Baltimore, MD, Total=$920.00, Items: laser printer",
    "Order 1029: Buyer=Caleb Young, Location=Albuquerque, NM, Total=$175.00, Items: ram upgrade kit",
    "Order 1030: Buyer=Isabelle King, Location=Tucson, AZ, Total=$530.00, Items: gaming headset, controller",
    "Order 1031: Buyer=Nathan Wright, Location=Fresno, CA, Total=$99.00, Items: usb-c hub, hdmi adapter",
    "Order 1032: Buyer=Zoe Harris, Location=Sacramento, CA, Total=$1380.00, Items: video capture card, streaming mic",
    "Order 1033: Buyer=Owen Campbell, Location=Raleigh, NC, Total=$275.00, Items: network switch",
    "Order 1034: Buyer=Ella Mitchell, Location=Omaha, NE, Total=$49.99, Items: screen protector film",
    "Order 1035: Buyer=Liam Carter, Location=Tulsa, OK, Total=$640.00, Items: smart tv mount, fire stick",
    "Order 1036: Buyer=Ava Phillips, Location=Cleveland, OH, Total=$815.00, Items: laptop cooling pad, ssd",
    "Order 1037: Buyer=Noah Evans, Location=Wichita, KS, Total=$130.00, Items: wireless charger, charging cable",
    "Order 1038: Buyer=Mia Turner, Location=Arlington, TX, Total=$3750.00, Items: server tower, ups battery",
    "Order 1039: Buyer=Aiden Collins, Location=Bakersfield, CA, Total=$210.00, Items: cable management kit",
    "Order 1040: Buyer=Layla Stewart, Location=Aurora, CO, Total=$460.00, Items: gaming chair",
    "Order 1041: Buyer=Lucas Sanchez, Location=Anaheim, CA, Total=$95.00, Items: bluetooth keyboard",
    "Order 1042: Buyer=Scarlett Morales, Location=Tampa, FL, Total=$1620.00, Items: 4k monitor, color calibrator",
    "Order 1043: Buyer=Elijah Rogers, Location=Santa Ana, CA, Total=$325.00, Items: webcam hd, green screen",
    "Order 1044: Buyer=Penelope Reed, Location=Corpus Christi, TX, Total=$72.00, Items: desk organizer, usb lamp",
    "Order 1045: Buyer=James Cook, Location=St. Louis, MO, Total=$870.00, Items: nvme ssd, m.2 enclosure",
    "Order 1046: Buyer=Luna Bailey, Location=Pittsburgh, PA, Total=$149.00, Items: smart plug set",
    "Order 1047: Buyer=Benjamin Rivera, Location=Anchorage, AK, Total=$2200.00, Items: nas drive array",
    "Order 1048: Buyer=Nora Richardson, Location=Stockton, CA, Total=$385.00, Items: vr headset accessories",
    "Order 1049: Buyer=Henry Patterson, Location=Henderson, NV, Total=$510.00, Items: graphics tablet, pen nibs",
    "Order 1050: Buyer=Aria Wood, Location=Cincinnati, OH, Total=$67.00, Items: laptop lock cable",
    "Order 1051: Buyer=Samuel Morgan, Location=Colorado Springs, CO, Total=$1890.00, Items: curved monitor, mount",
    "Order 1052: Buyer=Lily Bell, Location=Virginia Beach, VA, Total=$230.00, Items: portable monitor",
    "Order 1053: Buyer=David Murphy, Location=Riverside, CA, Total=$415.00, Items: gaming mouse, mousepad",
    "Order 1054: Buyer=Aubrey Powell, Location=New Orleans, LA, Total=$79.95, Items: cooling fan",
    "Order 1055: Buyer=Joseph Long, Location=Lexington, KY, Total=$960.00, Items: photo printer, ink set",
    "Order 1056: Buyer=Brooklyn Price, Location=Fort Worth, TX, Total=$540.00, Items: wireless headset",
    "Order 1057: Buyer=Christopher Barnes, Location=Madison, WI, Total=$188.00, Items: usb microphone",
    "Order 1058: Buyer=Savannah Ross, Location=El Paso, TX, Total=$1125.00, Items: rack mount switch, cables",
    "Order 1059: Buyer=Jack Henderson, Location=Lincoln, NE, Total=$345.00, Items: smart home hub, sensors",
    "Order 1060: Buyer=Leah Coleman, Location=Greensboro, NC, Total=$58.00, Items: screen wipe kit",
    "Order 1061: Buyer=Sebastian Jenkins, Location=Plano, TX, Total=$725.00, Items: projector screen",
    "Order 1062: Buyer=Zoey Perry, Location=Buffalo, NY, Total=$2900.00, Items: render farm node",
    "Order 1063: Buyer=Aiden Simmons, Location=Fort Wayne, IN, Total=$160.00, Items: power strip, timer",
    "Order 1064: Buyer=Paisley Foster, Location=Chandler, AZ, Total=$395.00, Items: color laser printer toner",
    "Order 1065: Buyer=Wyatt Bryant, Location=Scottsdale, AZ, Total=$1040.00, Items: ip camera system",
    "Order 1066: Buyer=Hazel Alexander, Location=Glendale, AZ, Total=$220.00, Items: smart bulbs pack",
    "Order 1067: Buyer=Carter Russell, Location=Tacoma, WA, Total=$475.00, Items: audio interface, xlr cable",
    "Order 1068: Buyer=Stella Griffin, Location=Providence, RI, Total=$89.00, Items: mini projector",
    "Order 1069: Buyer=Hudson Hayes, Location=Des Moines, IA, Total=$1355.00, Items: robot vacuum, mop attachment",
    "Order 1070: Buyer=Violet Myers, Location=Richmond, VA, Total=$310.00, Items: portable projector",
    "Order 1071: Buyer=Asher Diaz, Location=Spokane, WA, Total=$53.75, Items: usb fan, cable clips",
    "Order 1072: Buyer=Aurora Hunt, Location=Boise, ID, Total=$780.00, Items: espresso machine",
    "Order 1073: Buyer=Elias Grant, Location=Fremont, CA, Total=$2450.00, Items: high end gaming pc build",
    "Order 1074: Buyer=Bella Stone, Location=Columbus, GA, Total=$125.00, Items: fitness tracker",
    "Order 1075: Buyer=Julian Hawkins, Location=Fayetteville, NC, Total=$890.00, Items: studio monitors pair",
    "Order 1076: Buyer=Skylar Shaw, Location=Akron, OH, Total=$44.00, Items: phone stand, screen cloth",
    "Order 1077: Buyer=Cameron Duncan, Location=Montgomery, AL, Total=$565.00, Items: action camera, accessories",
    "Order 1078: Buyer=Mackenzie Warren, Location=Rochester, NY, Total=$1200.00, Items: midi controller, daw license",
    "Order 1079: Buyer=Eli Oliver, Location=Yonkers, NY, Total=$670.00, Items: android tablet, case",
    "Order 1080: Buyer=Peyton Mason, Location=Spokane Valley, WA, Total=$98.00, Items: surge protector bar",
    "Order 1081: Buyer=Sawyer Palmer, Location=Knoxville, TN, Total=$1580.00, Items: video conferencing kit",
    "Order 1082: Buyer=Kennedy Lane, Location=Springfield, MA, Total=$270.00, Items: smart thermostat",
    "Order 1083: Buyer=Quinn Gordon, Location=Orange, CA, Total=$490.00, Items: laser cutter materials",
    "Order 1084: Buyer=Rylee Warren, Location=Pasadena, CA, Total=$3100.00, Items: 3d printer, filament",
    "Order 1085: Buyer=Brody Price, Location=Bridgeport, CT, Total=$155.00, Items: ring light, tripod",
    "Order 1086: Buyer=Emery Hamilton, Location=Durham, NC, Total=$830.00, Items: smart lock set",
    "Order 1087: Buyer=Finley Butler, Location=Hampton, VA, Total=$72.50, Items: cable labels, velcro ties",
    "Order 1088: Buyer=Remi Burke, Location=Garland, TX, Total=$2650.00, Items: home theater system",
    "Order 1089: Buyer=Sloane Simmons, Location=Irving, TX, Total=$340.00, Items: biometric safe",
    "Order 1090: Buyer=Teagan Ford, Location=Gilbert, AZ, Total=$185.00, Items: car phone mount, dash cam",
    "Order 1091: Buyer=Rowan Cooper, Location=San Bernardino, CA, Total=$415.00, Items: outdoor security cam",
    "Order 1092: Buyer=Bellamy Kim, Location=Modesto, CA, Total=$60.00, Items: cable tester",
    "Order 1093: Buyer=Spencer Reed, Location=Fontana, CA, Total=$895.00, Items: digital piano",
    "Order 1094: Buyer=Harlow Diaz, Location=Moreno Valley, CA, Total=$1100.00, Items: air purifier, filter pack",
    "Order 1095: Buyer=Marlowe Price, Location=Glendale, CA, Total=$490.00, Items: smart doorbell, chime",
    "Order 1096: Buyer=Ronan Hughes, Location=Huntington Beach, CA, Total=$225.00, Items: solar panel charger",
    "Order 1097: Buyer=Indie Sanders, Location=Worcester, MA, Total=$760.00, Items: mesh wifi system",
    "Order 1098: Buyer=Zara Patterson, Location=Salt Lake City, UT, Total=$3400.00, Items: electric standing desk, mat",
    "Order 1099: Buyer=Leo Ward, Location=Tallahassee, FL, Total=$128.00, Items: smart plug, power meter",
    "Order 1100: Buyer=Nova Coleman, Location=Mobile, AL, Total=$575.00, Items: drone, extra battery",
    "Order 1101: Buyer=Jett Washington, Location=Shreveport, LA, Total=$220.00, Items: thermal label printer",
    "Order 1102: Buyer=Piper Murphy, Location=Augusta, GA, Total=$1680.00, Items: home gym equipment",
    "Order 1103: Buyer=Caiden Morris, Location=Little Rock, AR, Total=$390.00, Items: barcode scanner, labels",
    "Order 1104: Buyer=Birdie Ramirez, Location=Columbus, OH, Total=$85.00, Items: hdmi matrix switch",
    "Order 1105: Buyer=Cosmo Butler, Location=Huntsville, AL, Total=$940.00, Items: telescoping camera tripod"
]

@app.route("/api/orders", methods=["GET"])
def get_orders():
    """
    Returns orders as messy text. In real life, customers
    would have unpredictable formatting. The AI must parse it.
    """
    limit = request.args.get("limit", default=len(ORDERS), type=int)
    sample = random.sample(ORDERS, min(limit, len(ORDERS)))

    return jsonify({
        "status": "ok",
        "raw_orders": sample
    })


@app.route("/api/order/<order_id>", methods=["GET"])
def get_order_by_id(order_id):
    """
    Fetch a single order by scanning the text.
    """
    for text in ORDERS:
        if order_id in text:
            return jsonify({
                "status": "ok",
                "raw_order": text
            })

    return jsonify({"status": "not_found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)