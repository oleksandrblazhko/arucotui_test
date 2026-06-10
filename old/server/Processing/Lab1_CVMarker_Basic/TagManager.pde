class TagManager {
  Tag[] tags;
  PMatrix3D projectionMatrix;
  ArrayList<Integer> activeTags;

  TagManager(int n) {
    tags = new Tag[n];
    activeTags = new ArrayList<Integer>();
    for (int i = 0; i < n; i++) {
      tags[i] = new Tag(i);
    }
  }

  void set(int id, float tx, float ty, float tz, float rx, float ry, float rz, PVector[] corners) {
    tags[id].set(tx, ty, tz, rx, ry, rz, corners);
  }

  void update() {
    activeTags.clear();
    for (Tag t : this.tags) {
      t.checkActive();
      if (t.active) activeTags.add(t.id);
    }
  }

  void displayRaw(boolean flipped) {
    for (Tag t : tags) {
      if (t.active) {
        pushMatrix();
        pushStyle();
        noStroke();
        if (flipped == false) {
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
        } else {
          fill(255, 0, 0);
          ellipse(width-t.corners[0].x, t.corners[0].y, 5, 5);
          fill(255, 255, 0);
          ellipse(width-t.corners[1].x, t.corners[1].y, 5, 5);
          fill(0, 255, 255);
          ellipse(width-t.corners[2].x, t.corners[2].y, 5, 5);
          fill(0, 0, 255);
          ellipse(width-t.corners[3].x, t.corners[3].y, 5, 5);
          fill(0, 0, 255);
          beginShape();
          fill(255);
          stroke(0, 255, 0);
          for (int i = 0; i < 4; i++) {
            vertex(width-t.corners[i].x, t.corners[i].y);
          }
          endShape(CLOSE);
          fill(52);
          noStroke();
          PVector c = new PVector(width-(t.corners[0].x+t.corners[2].x)/2, (t.corners[0].y+t.corners[2].y)/2);
          String s = "(x,y)=("+nf(round(t.tx*100))+","+nf(round(t.ty*100))+")\nz="+nf(round(t.tz*100));
          textAlign(CENTER, CENTER);
          textSize(18);
          text("ID="+t.id+"\n"+s, c.x, c.y);
          popStyle();
          popMatrix();
        }
      }
    }
  }

  ArrayList<Tag> getActiveTags() {
    ArrayList<Tag> list = new ArrayList<Tag>();
    for (int tid : activeTags) list.add(tags[tid]);
    return list;
  }
}
