class TagManager {
  int TAG_D = 150;
  int TO_D = 150;
  Tag[] tags;
  ArrayList<TaggedObject> taggedObjects;
  PMatrix3D R1;
  PMatrix3D R2;
  ArrayList<Integer> activeTags;
  ArrayList<Integer> activeTOs;

  TagManager(int n, ArrayList to_ids, ArrayList to_offs) {
    tags = new Tag[n];
    this.taggedObjects = new ArrayList<TaggedObject>();
    activeTags = new ArrayList<Integer>();
    activeTOs = new ArrayList<Integer>();
    for (int i = 0; i < n; i++) {
      tags[i] = new Tag(i);
    }
    for (int i = 0; i < to_ids.size(); i++) {
      ArrayList<Integer> ids = (ArrayList<Integer>) to_ids.get(i);
      ArrayList<PVector> offs = (ArrayList<PVector>) to_offs.get(i);
      this.taggedObjects.add(new TaggedObject(ids, offs));
    }
  }

  void set(int id, float tx, float ty, float tz, float rx, float ry, float rz, PVector[] corners) {
    tags[id].set(tx, ty, tz, rx, ry, rz, corners);
  }

  void update() {
    activeTags.clear();
    activeTOs.clear();
    for (Tag t : this.tags) {
      t.checkActive();
      if (t.active) activeTags.add(t.id);
    }
    if (homographyMatrixCalculated) {
      for (TaggedObject _to : this.taggedObjects) {
        ArrayList<Tag> activeTags = new ArrayList<Tag>();
        for (Integer id : _to.ids) {
          if (tags[id].active) {
            activeTags.add(tags[id]);
          }
        }
        if (activeTags.size() > 0) {
          PVector loc = new PVector(0, 0, 0);
          PVector ori = new PVector(0, 0, 0);

          for (Tag t : activeTags) {
            PVector O = new PVector(t.tx, t.ty, t.tz);
            PVector offset = _to.getOffsetFromID(t.id);
            PVector v = new PVector(0, 0, offset.z);
            R1 = new PMatrix3D();
            R1.rotateZ(-t.rz);
            R1.rotateX(t.rx);
            R1.rotateY(t.ry);
            R1.rotateZ(t.rz);
            PVector rotated_v = new PVector();
            R1.mult(v, rotated_v);
            PVector P = new PVector(O.x - rotated_v.x, O.y + rotated_v.y, O.z + rotated_v.z); // x is inversed because of the inversed coordinate

            PVector w = new PVector(offset.x, offset.y, 0);
            R2 = new PMatrix3D();
            R2.rotateX(t.rx);
            R2.rotateY(t.ry);
            R2.rotateZ(t.rz);
            PVector rotated_w = new PVector();
            R2.mult(w, rotated_w);
            PVector P_prime = new PVector(P.x - rotated_w.x, P.y + rotated_w.y, P.z + rotated_w.z); // x is inversed because of the inversed coordinate
            loc.add(new PVector(P_prime.x, P_prime.y, P_prime.z));
            ori.add(new PVector(t.rx, t.ry, t.rz));
          }

          loc.div(activeTags.size());
          ori.div(activeTags.size());
          _to.set(loc.x, loc.y, loc.z, ori.x, ori.y, ori.z);
        } else {
          _to.setInactive();
        }
      }
      int i = 0;
      for (TaggedObject _to : this.taggedObjects) {
        if (_to.active) activeTOs.add(i);
        i++;
      }
    }
  }

  void displayRaw() {
    for (Tag t : tags) {
      if (t.active) {
        pushMatrix();
        pushStyle();
        noStroke();
        fill(255, 0, 0);
        ellipse(t.corners[0].x, t.corners[0].y, 5, 5);
        fill(255, 255, 0);
        ellipse(t.corners[1].x, t.corners[1].y, 5, 5);
        fill(0, 255, 255);
        ellipse(t.corners[2].x, t.corners[2].y, 5, 5);
        fill(0, 0, 255);
        ellipse(t.corners[3].x, t.corners[3].y, 5, 5);
        fill(0, 0, 255);


        beginShape();
        fill(255);
        stroke(0, 255, 0);
        for (int i = 0; i < 4; i++) {
          vertex(t.corners[i].x, t.corners[i].y);
        }
        endShape(CLOSE);

        fill(52);
        noStroke();

        PVector c = new PVector((t.corners[0].x+t.corners[2].x)/2, (t.corners[0].y+t.corners[2].y)/2);
        String s = "(x,y)=("+nf(round(t.tx*100))+","+nf(round(t.ty*100))+")\nz="+nf(round(t.tz*100));
        textAlign(CENTER, CENTER);
        textSize(18);
        text("ID="+t.id+"\n"+s, c.x, c.y);
        popStyle();
        popMatrix();
      }
    }
  }
  
  ArrayList<TaggedObject> getActiveTOs() {
    ArrayList<TaggedObject> list = new ArrayList<TaggedObject>();
    for (int to_id : activeTOs) list.add(taggedObjects.get(to_id));
    return list;
  }

  TaggedObject getBundle(int to_id) {
    TaggedObject to_x = null;
    ArrayList<TaggedObject> list = getActiveTOs();
    for (int i=0; i<list.size(); i++) {
      TaggedObject _to = list.get(i);
      for (int id : _to.ids) if (to_id==id) to_x=_to;
    }
    return to_x;
  }

  ArrayList<Tag> getActiveTags() {
    ArrayList<Tag> list = new ArrayList<Tag>();
    for (int tid : activeTags) list.add(tags[tid]);
    return list;
  }

  void drawActiveTOs(SimpleMatrix homography) {
    for (TaggedObject _to : getActiveTOs()) {
      float toD = TO_D;
      float angle2D = _to.rz-global_rz;
      //PVector tilt2D = new PVector(b.rx-global_rx,b.ry-global_ry);
      PVector tilt2D = new PVector(0, 0);
      PVector loc2D = img2screen(transformPoint(new PVector(_to.tx, _to.ty, _to.tz), homography));
      float distance = distancePointToPlane(new PVector(_to.tx, _to.ty, _to.tz), planePoints);
      if (distance<touchThreshold){ 
        drawTagSimple(_to.ids.get(0), loc2D, angle2D, tilt2D, toD, color(0, 127, 255, 52)); //example visualization
      }else{ 
        drawTagSimple(_to.ids.get(0), loc2D, angle2D, tilt2D, toD, color(0, 127, 255, 0)); //example visualization
      }
    }
  }
  
  void drawCustomActiveBundles(SimpleMatrix homography) {
    for (TaggedObject _to : getActiveTOs()) {
      float toD = TO_D;
      float angle2D = _to.rz-global_rz;
      //PVector tilt2D = new PVector(b.rx-global_rx,b.ry-global_ry);
      PVector tilt2D = new PVector(0, 0);
      PVector loc2D = img2screen(transformPoint(new PVector(_to.tx, _to.ty, _to.tz), homography));
      float distance = distancePointToPlane(new PVector(_to.tx, _to.ty, _to.tz), planePoints);
      if (distance<touchThreshold){ 
        drawTagCustom(_to.ids.get(0), loc2D, angle2D);
      }
    }
  }

  void drawActiveTags(SimpleMatrix homography) {
    for (Tag t : getActiveTags()) {
      if (!isCorner(t.id) && t.id !=0) {
        float tagD = TAG_D;
        float angle2D = t.rz-global_rz;
        //PVector tilt2D = new PVector(t.rx-global_rx,t.ry-global_ry);
        PVector tilt2D = new PVector(0, 0);
        PVector loc2D = img2screen(transformPoint(new PVector(t.tx, t.ty, t.tz), homography));
        float distance = distancePointToPlane(new PVector(t.tx, t.ty, t.tz), planePoints);
        if (distance<touchThreshold) drawTagSimple(t.id, loc2D, angle2D, tilt2D, tagD, color(100)); //example visualization
        else drawTagSimple(t.id, loc2D, angle2D, tilt2D, tagD, color(100, 100));
      }
    }
  }

  void drawTagSimple(int id, PVector loc2D, float angle2D, PVector tilt2D, float D, color c) {
    float R = D/2;
    if (R>=1) {
      pushMatrix();
      pushStyle();
      fill(c);
      strokeWeight(5);
      stroke(0);
      ellipse(loc2D.x, loc2D.y, D, D);
      line(loc2D.x, loc2D.y, loc2D.x + R * (cos(angle2D)), loc2D.y + R * (sin(angle2D)));
      //noFill();
      //ellipse(loc2D.x+R*sin(tilt2D.x), loc2D.y+R*sin(tilt2D.y), R, R);
      fill(255);
      noStroke();
      textSize(R);
      textAlign(CENTER, CENTER);
      text(id, loc2D.x, loc2D.y);
      fill(0);
      noStroke();
      textSize(R/3);
      textAlign(RIGHT, BOTTOM);
      text(id, loc2D.x+R, loc2D.y+R);
      popStyle();
      popMatrix();
    }
  }

  void drawTagCustom(int id, PVector loc2D, float angle2D) {
    int tagID = id;
    int R = 50;
    pushMatrix();
    pushStyle();
    fill(52);
    strokeWeight(5);
    stroke(0);
    ellipse(loc2D.x, loc2D.y, R*2, R*2);
    noStroke();
    ellipse(loc2D.x + R * (cos(angle2D)), loc2D.y + R * (sin(angle2D)), R/2, R/2);
    fill(255);
    noStroke();
    textSize(R/2);
    textAlign(CENTER, CENTER);
    text(id, loc2D.x-R, loc2D.y-R);
    popStyle();
    popMatrix();
  }
}
