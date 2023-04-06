# Using Open MQTT Gateway to parse Lora-Ben Messages

Using [OpenMQTTGateway](https://docs.openmqttgateway.com/) on a LILYGO card
bought at [AliExpress](https://www.aliexpress.us/item/2251832685763835.html?gatewayAdapt=bra2usa4itemAdapt&_randl_shipto=US)
or at [Amazon](https://a.co/d/dw0PhZ6).

```
LILYGO® TTGO LoRa32 V2.1_1.6 Version 915Mhz
ESP32 LoRa OLED 0.96 Inch SD Card Bluetooth WIFI Wireless Module ESP-32 SMA
SX1276 915MHz CH9102, China
```

Use this [youtube video as a reference](https://youtu.be/_gdXR1uklaY?t=110).
I am able to load the image `ttgo-lora32-v1-915` directly from the Chrome browser. Be aware that
this image does not take advantage of the OLED in this board, but its ease to use makes up
for that limitation. For a codebase that gives more control over the board, consider using
the [Xinyuan-LilyGO/LilyGo-LoRa-Series](https://github.com/Xinyuan-LilyGO/LilyGo-LoRa-Series.git) repo (see below).

**NOTE:** One caveat I hit when using the Mac OSX, was the need for installing the correct serial driver:

If you are on macOS and have a LilyGo LoRa32 V2.1 board, make sure you have the correct driver for the
[CH9102 Serial Chip installed](https://github.com/WCHSoftGroup/ch34xser_macos)
and selected in the popup when initiating the web install. To finalise
the driver installation don't forget the confirmation in the Security section of System Preferences after the restart.
The correct driver to then select in the popup of this web install is `/dev/cu.wchusbserialXXXXXXXXXXX`

After loading the firmware, [follow the steps described](https://docs.openmqttgateway.com/upload/portal.html)
in the OpenMQTTGateway site, so it can connect to an MQTT broker, and the desired MQTT topic.

This is what the payload will look like from the gateway:
    
```
{"rssi":-50,"snr":9.75,"pferror":-2189,"packetSize":49,"hex":"FF01000069643A35362C20626174743A332E363820762C2074656D703A36342E3420462C20646973743A31323137206D6D"}
```

To parse it, use the script as shown:

```bash
$ sudo apt install -y jq xxd
 
$ MQTT_BROKER=mqtt ; \
  PREFIX=lora/ESP32_LORA/LORAtoMQTT

$ mosquitto_sub -h $MQTT_BROKER -t ${PREFIX} | jq
{
  "rssi": -48,
  "snr": 9.5,
  "pferror": -3414,
  "packetSize": 50,
  "hex": "FF01000069643A3135362C20626174743A332E363820762C2074656D703A36362E3220462C20646973743A32383334206D6D"
}

$ mosquitto_sub -h $MQTT_BROKER -t ${PREFIX} | jq '.hex'
"FF01000069643A36302C20626174743A332E3638333220762C2074656D703A36362E3220462C20646973743A33303231206D6D"

$ while : ; do \
  mosquitto_sub -h $MQTT_BROKER -t ${PREFIX} -C 1 | jq --unbuffered '.hex' | xxd -r -p
  done
id:173, batt:3.6736 v, temp:66.2 F, dist:281 mm

$ while : ; do \
  MSG=$(mosquitto_sub -h $MQTT_BROKER -t ${PREFIX} -C 1 | jq --unbuffered '.hex' | xxd -r -p)
  MSG_ASCII="${MSG//[^[:ascii:]]/}"
  echo ${MSG_ASCII}
  DIST=$(echo ${MSG_ASCII} | cut -d, -f4 | cut -d' ' -f2 | cut -d: -f2)
  echo "Distance: ${DIST}"
  done
id:224, batt:3.68 v, temp:67.1 F, dist:271 mm
Distance: 271
```

## [Xinyuan-LilyGO / LilyGo-LoRa-Series](https://github.com/Xinyuan-LilyGO/LilyGo-LoRa-Series)

Tweaks in order to build LilyGo-LoRa-Series for this board via VScode:
    
```
$ cd LilyGo-LoRa-Series.git/

$ git rev-parse HEAD
fe64bb0ddfb3f46b284e694b55be23af9a23431f

$ git remote -v
origin  https://github.com/Xinyuan-LilyGO/LilyGo-LoRa-Series.git (fetch)
origin  https://github.com/Xinyuan-LilyGO/LilyGo-LoRa-Series.git (push)

$ git diff
diff --git a/examples/ArduinoLoRa/LoRaReceiver/utilities.h b/examples/ArduinoLoRa/LoRaReceiver/utilities.h
index c85dc3a..7f8a884 100644
--- a/examples/ArduinoLoRa/LoRaReceiver/utilities.h
+++ b/examples/ArduinoLoRa/LoRaReceiver/utilities.h
@@ -19,7 +19,8 @@
 * Option: 433E6,470E6,868E6,915E6
 * */

-#define LoRa_frequency      433E6
+#define LoRa_frequency      915E6


 #define UNUSE_PIN                   (0)
diff --git a/platformio.ini b/platformio.ini
index 32bf2ce..9e7aacf 100644
--- a/platformio.ini
+++ b/platformio.ini
@@ -22,15 +22,15 @@
 [platformio]
 ; default_envs = t3-v1.0
 ; default_envs = t3-v1.3
-; default_envs = t3-v1.6
+default_envs = t3-v1.6
 ; default_envs = t3-v1.8
 ; default_envs = t3-v2.0
 ; default_envs = t-beam-v0.7
 ; default_envs = t-beam-v1.x
-default_envs = t-beam-s3-core
+; default_envs = t-beam-s3-core
 ; default_envs = t3-s3-v1.0

-; src_dir = examples/ArduinoLoRa/LoRaReceiver
+src_dir = examples/ArduinoLoRa/LoRaReceiver
 ; src_dir = examples/ArduinoLoRa/LoRaSender
 ; src_dir = examples/GPS/UBlox_BasicNMEARead
 ; src_dir = examples/GPS/UBlox_NMEAParsing
@@ -94,12 +94,13 @@ monitor_filters =
        esp32_exception_decoder


-monitor_port = COM178
-upload_port  = COM178
+monitor_port = /dev/cu.wchusbserial56440061481
+upload_port  = /dev/tty.wchusbserial56440061481

 build_flags =
     ;define radio frequency
-    -DLoRa_frequency=868
+    ; -DLoRa_frequency=915E6


[esp32dev_base]
```

```
diff --git a/examples/ArduinoLoRa/LoRaReceiver/LoRaReceiver.ino b/examples/ArduinoLoRa/LoRaReceiver/LoRaReceiver.ino
index cd4101a..37701c1 100644
--- a/examples/ArduinoLoRa/LoRaReceiver/LoRaReceiver.ino
+++ b/examples/ArduinoLoRa/LoRaReceiver/LoRaReceiver.ino
@@ -26,12 +26,22 @@ void loop()
         Serial.print("Received packet '");

         String recv = "";
+        String recv2 = "";
+        int i;
         // read packet
         while (LoRa.available()) {
-            recv += (char)LoRa.read();
+            i = LoRa.read();
+            if (i > 31 && i < 128) {
+                if (recv.length() <= 24) {
+                    recv += (char)i;
+                } else {
+                    recv2 += (char)i;
+                }
+            }
         }

         Serial.println(recv);
+        Serial.println(recv2);

         // print RSSI of packet
         Serial.print("' with RSSI ");
@@ -40,12 +50,10 @@ void loop()
         if (u8g2) {
             u8g2->clearBuffer();
             char buf[256];
-            u8g2->drawStr(0, 12, "Received OK!");
-            u8g2->drawStr(0, 26, recv.c_str());
-            snprintf(buf, sizeof(buf), "RSSI:%i", LoRa.packetRssi());
-            u8g2->drawStr(0, 40, buf);
-            snprintf(buf, sizeof(buf), "SNR:%.1f", LoRa.packetSnr());
-            u8g2->drawStr(0, 56, buf);
+            u8g2->drawStr(0, 18, recv.c_str());
+            u8g2->drawStr(0, 33, recv2.c_str());
+            snprintf(buf, sizeof(buf), "RSSI:%i    SNR:%.1f", LoRa.packetRssi(), LoRa.packetSnr());
+            u8g2->drawStr(0, 60, buf);
             u8g2->sendBuffer();
         }
 #endif
```
