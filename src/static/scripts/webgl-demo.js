(async () => { const { initBuffers } = await import(initBuffersURL);})();
(async () => { const { drawScene } = await import(drawSceneURL);})();

const vs = `
attribute vec4 a_position;
attribute vec3 a_normal;
 
uniform mat4 u_projection;
uniform mat4 u_view;
uniform mat4 u_world;
 
varying vec3 v_normal;
 
void main() {
  gl_Position = u_projection * u_view * u_world * a_position;
  v_normal = mat3(u_world) * a_normal;
}`;
 
const fs = `
precision mediump float;
 
varying vec3 v_normal;
 
uniform vec4 u_diffuse;
uniform vec3 u_lightDirection;
 
void main () {
  vec3 normal = normalize(v_normal);
  float fakeLight = dot(u_lightDirection, normal) * .5 + .5;
  gl_FragColor = vec4(u_diffuse.rgb * fakeLight, u_diffuse.a);
}`;

const modelPath = "./static/model/rocket_edited.obj";
const framerate = 10; // 1/10 of a second.

class Quaternion {
  constructor(w, x, y, z) {
    this.w = w;
    this.x = x;
    this.y = y;
    this.z = z;
  }

  //Quaternion to Euler from Wikipedia (does NOT account for gimbal lock)
  toEulerBasic() {
    let angles = new Euler();
    
    //roll
    let sinr_cosp = 2 * (this.w * this.x + this.y * this.z);
    let cosr_cosp = 1 - 2 * (this.x * this.x + this.y * this.y);
    angles.roll = Math.atan2(sinr_cosp, cosr_cosp);

    //pitch
    let sinp = Math.sqrt(1 + 2 * (this.w * this.y - this.x * this.z));
    let cosp = Math.sqrt(1 - 2 * (this.w * this.y - this.x * this.z));
    angles.pitch = 2 * Math.atan2(sinp, cosp) - Math.PI / 2;

    //yaw
    let siny_cosp = 2 * (this.w * this.z + this.x * this.y);
    let cosy_cosp = 1 - 2 * (this.y * this.y + this.z * this.z);
    angles.yaw = Math.atan2(siny_cosp, cosy_cosp);

    return angles;
  }

  //accounting for gimbal lock (for normalized quaternions)
  toEulerNormalized() {
    let angles = new Euler();

    let test = this.x * this.y + this.z * this.w;
    //singularity at north pole (santa's in trouble 😱)
    if(test > 0.499) {
      angles.yaw = 2 * Math.atan2(this.x, this.w);
      angles.pitch = Math.PI/2;
      angles.roll = 0;
    } 

    //singularity at south pole (..evil santa is in trouble 🤨)
    else if(test < -0.499) {
      angles.yaw = -2 * Math.atan2(this.x, this.w);
      angles.pitch = -Math.PI/2
      angles.bank = 0;
    } 

    else {
      let sqx = this.x * this.x;
      let sqy = this.y * this.y;
      let sqz = this.z * this.z;
      angles.yaw = Math.atan2(2 * this.y * this.w - 2 * this.x * this.z, 1 - 2 * sqy - 2 * sqz);
      angles.pitch = Math.asin(2 * test);
      angles.roll = Math.atan2(2 * this.x * this.w - 2 * this.y * this.z, 1 - 2 * sqx - 2 * sqz);
    }

    return angles;
  }

  //accounting for gimbal lock (for non normalized quaternions)
  toEulerNonNormalized() {
    let angles = new Euler();

    let sqx = this.x * this.x;
    let sqy = this.y * this.y;
    let sqz = this.z * this.z;
    let sqw = this.w * this.w;

    let unit = sqx + sqy + sqz + sqw;
    let test = this.x * this.y + this.z * this.w;

    //singularity at north pole (santa's in trouble 😱)
    if(test > 0.499 * unit) {
      angles.yaw = 2 * Math.atan2(this.x, this.w);
      angles.pitch = Math.PI/2;
      angles.roll = 0;
    } 

    //singularity at south pole (..evil santa is in trouble 🤨)
    else if(test < -0.499 * unit) {
      angles.yaw = -2 * Math.atan2(this.x, this.w);
      angles.pitch = -Math.PI/2
      angles.bank = 0;
    } 

    else {
      angles.yaw = Math.atan2(2 * this.y * this.w - 2 * this.x * this.z, sqx - sqy - sqz + sqw);
      angles.pitch = Math.asin(2 * test);
      angles.roll = Math.atan2(2 * this.x * this.w - 2 * this.y * this.z, -sqx + sqy - sqz + sqw);
    }

    return angles;
  }

}

function Euler(roll, pitch, yaw) {
  this.roll = roll;
  this.pitch = pitch;
  this.yaw = yaw;
}

main();

//
// start here
//
async function main() {

  const canvas = document.querySelector("#gl-canvas");
  // Initialize the GL context
  const gl = canvas.getContext("webgl");

  // Only continue if WebGL is available and working
  if (gl === null) {
    alert(
      "Unable to initialize WebGL. Your browser or machine may not support it.",
    );
    return;
  }

  const response = await (modelPath); //RELATIVE URL...
  const text = await response.text();
  const data = parseOBJ(text);

  // Set clear color to black, fully opaque
  gl.clearColor(0.0, 0.0, 0.0, 1.0);
  // Clear the color buffer with specified clear color
  gl.clear(gl.COLOR_BUFFER_BIT);

  const parts = data.geometries.map(({data}) => {
    const bufferInfo = webglUtils.createBufferInfoFromArrays(gl, data);
    return {
      material: {
        u_diffuse: [Math.random(), Math.random(), Math.random(), 1],
      },
      bufferInfo,
    };
  });

  const meshProgramInfo = webglUtils.createProgramInfo(gl, [vs, fs]);

  const cameraTarget = [0, 2, 0];
  const cameraPosition = [0, 0, 30];
  const zNear = 0.1;
  const zFar = 100;

  function degToRad(deg) {
    return deg * Math.PI / 180;
  }

  function radToDeg(radians) { 
    const degrees = radians * (180 / Math.PI);
    return degrees;
  }

  let prev = 0;
  const fpsCounter = document.querySelector("#fps");
  let framecounter = 0;

  function render(time) {
    time *= 0.001;  // convert to seconds
    const deltaTime = time - prev;
    prev = time;
    const fps = 1/deltaTime;
    fpsCounter.textContent = fps.toFixed(0);
    //console.log("changed to " + angleX);
    webglUtils.resizeCanvasToDisplaySize(gl.canvas);
    gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);
    gl.enable(gl.DEPTH_TEST);
    gl.enable(gl.CULL_FACE);
 
    const fieldOfViewRadians = degToRad(60);
    const aspect = gl.canvas.clientWidth / gl.canvas.clientHeight;
    const projection = m4.perspective(fieldOfViewRadians, aspect, zNear, zFar);
 
    const up = [0, 1, 0];
    // Compute the camera's matrix using look at.
    const camera = m4.lookAt(cameraPosition, cameraTarget, up);
 
    // Make a view matrix from the camera matrix.
    const view = m4.inverse(camera);
 
    const sharedUniforms = {
      u_lightDirection: m4.normalize([-1, 3, 5]),
      u_view: view,
      u_projection: projection,
    };
 
    gl.useProgram(meshProgramInfo.program);
 
    // calls gl.uniform
    webglUtils.setUniforms(meshProgramInfo, sharedUniforms);
    // compute the world matrix once since all parts
    // are at the same space.
    
    rotationIndex = ((framecounter % framerate == 0) ? (rotationIndex + 1) : (rotationIndex));
    
    let tempW = Number(document.getElementById("input_data").getAttribute("w_in"));
    let tempX = Number(document.getElementById("input_data").getAttribute("x_in"));
    let tempY = Number(document.getElementById("input_data").getAttribute("y_in"));
    let tempZ = Number(document.getElementById("input_data").getAttribute("z_in"));
    let tempquat = new Quaternion(tempW, tempX, tempY, tempZ);
    let tempeul = tempquat.toEulerNormalized();
    
    let u_world = new Float32Array([ 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]);//make empty rotation matrix
    document.getElementById("xAngle").textContent = radToDeg(angleX) + " Degrees";
    document.getElementById("yAngle").textContent = radToDeg(angleY) + " Degrees";
    document.getElementById("zAngle").textContent = radToDeg(angleZ) + " Degrees";
    u_world = m4.xRotate(u_world, angleX);
    u_world = m4.yRotate(u_world, angleY);
    u_world = m4.zRotate(u_world, angleZ);

 
    for (const {bufferInfo, material} of parts) {
      // calls gl.bindBuffer, gl.enableVertexAttribArray, gl.vertexAttribPointer
      webglUtils.setBuffersAndAttributes(gl, meshProgramInfo, bufferInfo);
  
      // calls gl.uniform
      webglUtils.setUniforms(meshProgramInfo, {
        u_world,
        u_diffuse: material.u_diffuse,
      });
  
      // calls gl.drawArrays or gl.drawElements
      webglUtils.drawBufferInfo(gl, bufferInfo);
    }
    framecounter++;
    requestAnimationFrame(render);
  }
  requestAnimationFrame(render);
}

function parseOBJ(text) {
  // because indices are base 1 let's just fill in the 0th data
  const objPositions = [[0, 0, 0]];
  const objTexcoords = [[0, 0]];
  const objNormals = [[0, 0, 0]];

  // same order as `f` indices
  const objVertexData = [
    objPositions,
    objTexcoords,
    objNormals,
  ];

  // same order as `f` indices
  let webglVertexData = [
    [],   // positions
    [],   // texcoords
    [],   // normals
  ];
  const materialLibs = [];
  const geometries = [];
  let groups = ['default'];
  let geometry;
  let material = 'default';
  let object = 'default';
 
  function newGeometry() {
    // If there is an existing geometry and it's
    // not empty then start a new one.
    if (geometry && geometry.data.position.length) {
      geometry = undefined;
    }
  }
 
  function setGeometry() {
    if (!geometry) {
      const position = [];
      const texcoord = [];
      const normal = [];
      webglVertexData = [
        position,
        texcoord,
        normal,
      ];
      geometry = {
        object,
        groups,
        material,
        data: {
          position,
          texcoord,
          normal,
        },
      };
      geometries.push(geometry);
    }
  }

  function addVertex(vert) {
    const ptn = vert.split('/');
    ptn.forEach((objIndexStr, i) => {
      if (!objIndexStr) {
        return;
      }
      const objIndex = parseInt(objIndexStr);
      const index = objIndex + (objIndex >= 0 ? 0 : objVertexData[i].length);
      webglVertexData[i].push(...objVertexData[i][index]);
    });
  }

  const noop = () => {};

  const keywords = {
    v(parts) {
      setGeometry();
      objPositions.push(parts.map(parseFloat));
    },
    vn(parts) {
      objNormals.push(parts.map(parseFloat));
    },
    vt(parts) {
      // should check for missing v and extra w?
      objTexcoords.push(parts.map(parseFloat));
    },
    f(parts) {
      const numTriangles = parts.length - 2;
      for (let tri = 0; tri < numTriangles; ++tri) {
        addVertex(parts[0]);
        addVertex(parts[tri + 1]);
        addVertex(parts[tri + 2]);
      }
    },
    g(parts) {
      groups = parts;
      newGeometry()
    },
    s: noop,
    mtllib(parts, unparsedArgs) {
      materialLibs.push(unparsedArgs);
    },
    o(parts, unparsedArgs) {
      object = unparsedArgs;
      newGeometry();
    },
    usemtl(parts, unparsedArgs) {
      material = unparsedArgs;
      newGeometry();
    },
  };
  
  const keywordRE = /(\w*)(?: )*(.*)/;
  const lines = text.split('\n');
  for (let lineNo = 0; lineNo < lines.length; ++lineNo) {
    const line = lines[lineNo].trim();
    if (line === '' || line.startsWith('#')) {
      continue;
    }
    const m = keywordRE.exec(line);
    if (!m) {
      continue;
    }
    const [, keyword, unparsedArgs] = m;
    const parts = line.split(/\s+/).slice(1);
    const handler = keywords[keyword];
    if (!handler) {
      console.warn('unhandled keyword:', keyword);  // eslint-disable-line no-console
      continue;
    }
    handler(parts, unparsedArgs);
  }

    // remove any arrays that have no entries.
  for (const geometry of geometries) {
    geometry.data = Object.fromEntries(
        Object.entries(geometry.data).filter(([, array]) => array.length > 0));
  }
 
  return {
    materialLibs,
    geometries,
  };
}