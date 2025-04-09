#!/usr/bin/env bash
# upload a sliced project file and start the print immediately
set -eu

# read variables in script directory
dir="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")" )"
source "$dir/.env"

# file to upload
file="${1:?file *.gcode.3mf required}"
name=$(basename "$file")
if ! [[ $name =~ \.gcode\.3mf$ ]]; then
  echo "please use a *.gcode.3mf file!"
fi

# be verbose from here on
set -x

# upload with curl
curl --ftp-pasv --insecure \
  "ftps://$BAMBU_HOSTNAME/" \
  --user "bblp:$BAMBU_ACCESS_CODE" \
  -T "$file"

# request the print through mqtt
mosquitto_pub --insecure --cafile "$dir/bambu-ca.pem" \
  -L "mqtts://bblp:$BAMBU_ACCESS_CODE@$BAMBU_HOSTNAME/device/$BAMBU_SERIAL/request" \
  -m "$(jq -nr --arg name "$name" '{
    print: {
      command: "project_file",
      subtask_name: $name,
      url: ("file:///sdcard/" + $name),
      param: "Metadata/plate_1.gcode",
      subtask_id: "0",
      use_ams: false,
      timelapse: false,
      flow_cali: true,
      bed_leveling: true,
      layer_inspect: false,
      vibration_cali: false
    }}')"
