//Event listeners
void Tag_Present3D(int id, float tx, float ty, float tz, float rx, float ry, float rz) {
    if (serialDebug && id!=0) println("+ Tag:", id, "loc = (", tx, ",", ty, ",", tz, "), angle = (", degrees(rx),",",degrees(ry),",",degrees(rz),")");
}

void Tag_Absent3D(int id, float tx, float ty, float tz, float rx, float ry, float rz) {
    if (serialDebug && id!=0) println("- Tag:", id, "loc = (", tx, ",", ty, ",", tz,"), angle = (", degrees(rx),",",degrees(ry),",",degrees(rz),")");
}

void Tag_Update3D(int id, float tx, float ty, float tz, float rx, float ry, float rz) {
    if (serialDebug &&id!=0) println("% Tag:", id, "loc = (", tx, ",", ty, ",", tz,"), angle = (", degrees(rx),",",degrees(ry),",",degrees(rz),")");
}

//added in Lab2
void TO_Present2D(int id, float x, float y, float z, float rz) {
  if (serialDebug && homographyMatrixCalculated && !isCorner(id)) {
    PVector t = img2screen(transformPoint(new PVector(x, y, z), homography));
    println("+ Bundle:", id, "loc = (", t.x, ",", t.y, "), angle = ", degrees(rz));
  }
  if (homographyMatrixCalculated && !isCorner(id)) {
    PVector t = img2screen(transformPoint(new PVector(x, y, z), homography));
    for (DataObject obj : DOlist) {
      if (obj.checkHit(t.x, t.y, tm.TO_D/2)) {
        if (!obj.hasCtrlID(id)) {
          obj.addCtrlID(id, new PVector(t.x,t.y), rz);
        }
      }
    }
  }
}

void TO_Absent2D(int id, float x, float y, float z, float rz) {
  if (serialDebug && homographyMatrixCalculated && !isCorner(id)) {
    PVector t = img2screen(transformPoint(new PVector(x, y, z), homography));
    println("- Bundle:", id, "loc = (", t.x, ",", t.y, "), angle = ", degrees(rz));
  }
  if (homographyMatrixCalculated && !isCorner(id)) {
    PVector t = img2screen(transformPoint(new PVector(x, y, z), homography));
    for (DataObject obj : DOlist) {
      if (obj.hasCtrlID(id)) {
        obj.setPreviousRotation(obj.rotation);
        obj.removeCtrlID(id);
      }
    }
  }
}

void TO_Update2D(int id, float x, float y, float z, float rz) {
  if (serialDebug && homographyMatrixCalculated && !isCorner(id)) {
    PVector t = img2screen(transformPoint(new PVector(x, y, z), homography));
    println("- Bundle:", id, "loc = (", t.x, ",", t.y, "), angle = ", degrees(rz));
  }
  if (homographyMatrixCalculated && !isCorner(id)) {
    PVector t = img2screen(transformPoint(new PVector(x, y, z), homography));
    for (DataObject obj : DOlist) {
      if (obj.hasCtrlID(id)) {
        
      }
    }
  }
}
