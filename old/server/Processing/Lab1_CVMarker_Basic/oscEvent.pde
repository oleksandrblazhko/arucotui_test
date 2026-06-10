void oscEvent(OscMessage msg) {
  if (msg.checkAddrPattern("/marker")) {
    int id = msg.get(0).intValue();
    float tx = msg.get(1).floatValue();
    float ty = msg.get(2).floatValue();
    float tz = msg.get(3).floatValue();
    float rx = msg.get(4).floatValue();
    float ry = msg.get(5).floatValue();
    float rz = msg.get(6).floatValue();
    float p1x = msg.get(7).intValue();
    float p1y = msg.get(8).intValue();
    float p2x = msg.get(9).intValue();
    float p2y = msg.get(10).intValue();
    float p3x = msg.get(11).intValue();
    float p3y = msg.get(12).intValue();
    float p4x = msg.get(13).intValue();
    float p4y = msg.get(14).intValue();
    PVector[] corners = {new PVector(p1x,p1y),new PVector(p2x,p2y),new PVector(p3x,p3y),new PVector(p4x,p4y)};
    tm.set(id, tx, ty, tz, rx, ry, rz, corners);
  }
}
