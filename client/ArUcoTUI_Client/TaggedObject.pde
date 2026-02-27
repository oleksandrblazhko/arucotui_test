class TaggedObject {
  int TTL = 100;
  boolean active;
  long ts;
  ArrayList<Integer> ids;
  ArrayList<PVector> offs;
  float tx, ty, tz, rx, ry, rz;
  float p_rx, p_ry, p_rz;

  TaggedObject(ArrayList<Integer> TO_IDs, ArrayList<PVector> IDoffsets) {
    this.ids = new ArrayList<Integer>();
    this.offs = new ArrayList<PVector>();
    for (int i = 0; i < TO_IDs.size(); i++) {
      this.ids.add(TO_IDs.get(i));
      this.offs.add(IDoffsets.get(i));
    }
    this.tx = 0;
    this.ty = 0;
    this.tz = 0;
    this.rx = 0;
    this.ry = 0;
    this.rz = 0;
    this.ts = 0;
    this.active = false;
  }

  void setInactive() {
    if (this.active && (millis()-this.ts)>this.TTL) {
      this.active = false;
      TO_Absent2D(this.getTO_ID(), this.tx, this.ty, this.tz, this.rz);
    }
  }

  float unwrapAngle(float currentAngle, float previousAngle) {
    float deltaAngle = currentAngle - previousAngle;
    if (deltaAngle > PI) {
      currentAngle -= TWO_PI;
    } else if (deltaAngle < -PI) {
      currentAngle += TWO_PI;
    }
    return currentAngle;
  }

  void set(float tx, float ty, float tz, float rx, float ry, float rz) {
    boolean update = true;
    this.tx = tx;
    this.ty = ty;
    this.tz = tz;
    this.rx = unwrapAngle(rx, p_rx);
    this.ry = unwrapAngle(ry, p_ry);
    this.rz = unwrapAngle(rz, p_rz);
    
    float distance = distancePointToPlane(new PVector(tx, ty, tz), planePoints);
    if (distance<touchThreshold) {
      if (!this.active) {
        TO_Present2D(this.getTO_ID(), this.tx, this.ty, this.tz, this.rz);
      } else {
        TO_Update2D(this.getTO_ID(), this.tx, this.ty, this.tz, this.rz);
      }
      this.active = true;
      this.ts = millis();
    } else {
      if (this.active && (millis()-this.ts)>this.TTL) {
        this.active = false;
        TO_Absent2D(this.getTO_ID(), this.tx, this.ty, this.tz, this.rz);
      }
    }
  }

  int getTO_ID() {
    return this.ids.get(0);
  }

  PVector getScreenLoc2D(SimpleMatrix homography) {
    return img2screen(transformPoint(new PVector(this.tx, this.ty, this.tz), homography));
  }

  PVector getOffsetFromID (int targetID) {
    int index = -1;
    for (int i = 0; i < this.ids.size(); i++) {
      if (this.ids.get(i) == targetID) {
        index = i;
        break;
      }
    }
    if (index>=0) return this.offs.get(index);
    else return new PVector(0, 0, 0);
  }
}
