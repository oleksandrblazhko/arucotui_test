void DO_setValue(int dataID, int ctrlID) {
  DataObject obj = DOlist.get(dataID);
  obj.setTempVal(map(degrees(obj.rotation-obj.prev_rotation), 0, 100, 0, 10));
}

void DO_setValueLoc2D(int dataID, int ctrlID) {
  DataObject obj = DOlist.get(dataID);
  TaggedObject b = tm.getBundle(ctrlID);
  if (b!=null) {
    PVector loc2D = img2screen(transformPoint(new PVector(b.tx, b.ty, b.tz), homography));
    obj.setTempVal(map(degrees(obj.rotation-obj.prev_rotation), 0, 100, 0, 10));
    obj.updateLoc2D(loc2D.x, loc2D.y);
  }
}

void DO_setLocOri2D(int dataID, int ctrlID) {
  DataObject obj = DOlist.get(dataID);
  TaggedObject b = tm.getBundle(ctrlID);
  if (b!=null) {
    PVector loc2D = img2screen(transformPoint(new PVector(b.tx, b.ty, b.tz), homography));
    obj.updateLoc2D(loc2D.x, loc2D.y);
    obj.updateOri2D(obj.rotation); //relative rotation (as a knob)
  }
}
