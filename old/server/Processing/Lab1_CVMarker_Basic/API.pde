void initTagManager() {
  tm = new TagManager(600);
}

//Event listeners
void tagPresent3D(int id, float tx, float ty, float tz, float rx, float ry, float rz) {
    println("+ Tag:", id, "loc = (", tx, ",", ty, ",", tz, "), angle = (", degrees(rx),",",degrees(ry),",",degrees(rz),")");
    if(id>=10 && id <=21) dataObjects[id-10] = 1;
}

void tagAbsent3D(int id, float tx, float ty, float tz, float rx, float ry, float rz) {
    println("- Tag:", id, "loc = (", tx, ",", ty, ",", tz,"), angle = (", degrees(rx),",",degrees(ry),",",degrees(rz),")");
    if(id>=10 && id <=21) dataObjects[id-10] = 0;
}

void tagUpdate3D(int id, float tx, float ty, float tz, float rx, float ry, float rz) {
    //println("% Tag:", id, "loc = (", tx, ",", ty, ",", tz,"), angle = (", degrees(rx),",",degrees(ry),",",degrees(rz),")");
}
