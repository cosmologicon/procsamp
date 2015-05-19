var tau = 6.283185307179586
function clamp(x, a, b) { return x < a ? a : x > b ? b : x }
var C = 128, samples_per_chunk = C
var P = 128, chunks_per_window = P
var Q = 256, frequencies_sampled = Q
var F = 32768, samples_per_second = F
var L = F / 64, samples_per_slice = L
var Sw = 256
var hmin = -40, hmax = 24

function init() {
	gl = UFX.gl(canvas)
	rawscape = makedatatexture(C, P, gl.LUMINANCE)
	chunkscape = makedatafbo(P, Q)
	specscape = makedatafbo(Sw, Q)
	gl.addProgram("dump", "vfill", "fdump")
	gl.addProgram("chunk", "vfill", "fchunk")
	gl.addProgram("spec", "vfill", "fspec")

	acontext = new AudioContext()
}
function dump(texture) {
	gl.resize(texture.w, texture.h)
	gl.clearColor(0, 0, 0, 1)
	gl.clear(gl.COLOR_BUFFER_BIT)
	gl.disable(gl.DEPTH_TEST)
	gl.progs.dump.use()
	gl.activeTexture(gl.TEXTURE0)
	gl.bindTexture(gl.TEXTURE_2D, texture)
	gl.progs.dump.set({
		texture: 0,
		viewportsize: [texture.w, texture.h],
	})
	gl.drawArrays(gl.POINTS, 0, 1)
}
function makedatatexture(w, h, format) {
	var texture = gl.createTexture()
	gl.bindTexture(gl.TEXTURE_2D, texture)
	gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST)
	gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST)
	gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
	gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
	gl.texImage2D(gl.TEXTURE_2D, 0, format, w, h, 0, format, gl.UNSIGNED_BYTE, null)
	texture.w = w
	texture.h = h
	return texture
}
function makedatafbo(w, h) {
	var fbo = gl.createFramebuffer()
	fbo.texture = makedatatexture(w, h, gl.RGBA)
	return fbo
}
function bindfbo(fbo) {
	if (fbo) {
		gl.bindFramebuffer(gl.FRAMEBUFFER, fbo)
		gl.bindTexture(gl.TEXTURE_2D, fbo.texture)
		gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, fbo.texture, 0)
		gl.viewport(0, 0, fbo.texture.w, fbo.texture.h)
	} else {
		gl.bindFramebuffer(gl.FRAMEBUFFER, null)
		gl.viewport(0, 0, gl.canvas.width, gl.canvas.height)
	}
}
function filldatatexture(texture, data, offset) {
	gl.bindTexture(gl.TEXTURE_2D, texture)
	if (data.length != texture.w * texture.h || offset) {
		offset = offset || 0
		n = Math.min(texture.w * texture.h, data.length - offset)
		data = data.subarray(offset, offset + n)
	}
	gl.texImage2D(gl.TEXTURE_2D, 0, gl.LUMINANCE, texture.w, texture.h, 0, gl.LUMINANCE,
		gl.UNSIGNED_BYTE, data)
}
function renderchunks() {
	bindfbo(chunkscape)
	gl.clear(gl.COLOR_BUFFER_BIT)
	gl.progs.chunk.use()
	gl.activeTexture(gl.TEXTURE0)
	gl.bindTexture(gl.TEXTURE_2D, rawscape)
	gl.progs.chunk.set({
		rawscape: 0,
		rawscapesize: [rawscape.w, rawscape.h],
		viewportsize: [chunkscape.texture.w, chunkscape.texture.h],
		hmin: hmin,
		hmax: hmax,
		F: F,
	})
	gl.drawArrays(gl.POINTS, 0, 1)
	bindfbo()
}
function renderspec(x) {
	bindfbo(specscape)
	gl.viewport(x, 0, 1, Q)
	gl.scissor(x, 0, 1, Q)
	gl.enable(gl.SCISSOR_TEST)
	gl.progs.spec.use()
	gl.activeTexture(gl.TEXTURE0)
	gl.bindTexture(gl.TEXTURE_2D, chunkscape.texture)
	gl.progs.spec.set({
		chunkscape: 0,
		chunkscapesize: [chunkscape.texture.w, chunkscape.texture.h],
		viewportsize: [1, Q],
	})
	gl.drawArrays(gl.POINTS, 0, 1)
	bindfbo()
	gl.disable(gl.SCISSOR_TEST)
}
function renderslice(data, jslice) {
	filldatatexture(rawscape, data, L * jslice)
	renderchunks()
	renderspec(jslice)
}

function handleupload(transfer) {
	if (!transfer.files.length == 1) throw "drag 1 file please"
	var reader = new FileReader()
	reader.addEventListener("load", function (event) {
		acontext.decodeAudioData(event.target.result, handledecode)
	}, false)
	reader.readAsArrayBuffer(transfer.files[0])
}
function getmergedchannels(buffer) {
	var channeldata = [], nchannels = buffer.numberOfChannels
	for (var i = 0 ; i < nchannels ; ++i) {
		channeldata.push(buffer.getChannelData(i))
	}
	for (var i = 1 ; i < nchannels ; ++i) {
		for (var j = 0 ; j < channeldata[0].length ; ++j) {
			channeldata[0][j] += channeldata[i][j]
		}
	}
	for (var j = 0 ; j < channeldata[0].length ; ++j) {
		channeldata[0][j] /= nchannels
	}
	return channeldata[0]
}
function resample(a, Fi) {
	Ni = a.length
	N = Math.floor(Ni * F / Fi)
	var u = new Uint8Array(N)
	for (var k = 0 ; k < N ; ++k) {
		var j = Math.floor(k * Fi / F)
		var x = (a[j] + 1) * 127.5
		u[k] = clamp(Math.floor(x), 0, 255)
	}
	return u
}
function handledecode(buffer) {
	var a = getmergedchannels(buffer)
	var u = resample(a, buffer.sampleRate)
	for (var x = 0 ; x < 256 ; ++x) renderslice(u, x)
}


// convert between frequency and h-value
function htof(h) {
	return 440 * Math.exp(h * Math.log(2) / 12)
}
function ftoh(f) {
	return Math.log(f / 440) * 12 / Math.log(2)
}

