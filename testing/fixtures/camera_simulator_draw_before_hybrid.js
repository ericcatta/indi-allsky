// Frozen drawing routine from e481b884; used only for parity.
function pixels2mm(pixels, pixel_um) {
    return pixels * (pixel_um / 1000);
}

function show_simulation() {
    lens = $("#LENS_SELECT").val();
    sensor = $("#SENSOR_SELECT").val();

    const canvas = document.getElementById("image-circle-canvas");
    const ctx = canvas.getContext("2d");

    // All geometry values are in millimeters

    // sensor rectangle
    var r = {
        w : pixels2mm(sd[sensor]['w'], sd[sensor]['p']),
        h : pixels2mm(sd[sensor]['h'], sd[sensor]['p']),
    };

    // image circle
    var c = {
        r : icd[lens] / 2,
    };

    //console.log('Sensor rect: ' + r.w + ' x ' + r.h)
    //console.log('Image circle: ' + c.r)

    var offset_x = pixels2mm($("#OFFSET_X").val(), sd[sensor]['p']);
    var offset_y = pixels2mm($("#OFFSET_Y").val(), sd[sensor]['p']);

    // clear canvas
    canvas.setAttribute("width", window.innerWidth);
    canvas.setAttribute("height", window.innerHeight);
    var hRatio = canvas.width  / r['w'];
    var vRatio = canvas.height / r['h'];
    var ratio  = Math.min ( hRatio, vRatio );
    //console.log('Ratio: ' + ratio);

    canvas.width = r.w * ratio;
    canvas.height = r.h * ratio;

    ctx.beginPath();
    ctx.fillStyle="#000000";
    ctx.rect(
        0,
        0,
        r.w * ratio,
        r.h * ratio
    );
    ctx.stroke();
    ctx.fill();

    ctx.beginPath();
    ctx.fillStyle="#444444";
    ctx.globalCompositeOperation="source-atop";
    //ctx.globalCompositeOperation="source-bottom";
    ctx.arc(
        ((r.w / 2) + offset_x) * ratio,
        ((r.h / 2) - offset_y) * ratio,
        c.r * ratio,
        0,
        2 * Math.PI,
        false
    );
    ctx.stroke();
    ctx.fill();


    ctx.font = '20px serif';
    ctx.textAlign = 'center';


    var circle_list = [
        [80, 87],
        [70, 80],
        [60, 69],
        [50, 57],
        [40, 45],
        [30, 33],
        [20, 21],
        [10, 10],
    ]

    circle_list.forEach(function (item, index) {
        ctx.beginPath();
        ctx.fillStyle="#333333";
        ctx.arc(
            ((r.w / 2) + offset_x) * ratio,
            ((r.h / 2) - offset_y) * ratio,
            (c.r * ((10 / 9) * (item[1] / 100))) * ratio,
            0,
            2 * Math.PI,
            false
        );
        ctx.stroke();

        ctx.strokeText(item[0] * 2 + "°", ((r.w / 2) - (c.r * ((10 / 9) * (item[1] / 100))) + offset_x) * ratio + 20, ((r.h / 2) - offset_y) * ratio);
        ctx.strokeText(item[0] * 2 + "°", ((r.w / 2) + offset_x) * ratio, ((r.h / 2) - (c.r * ((10 / 9) * (item[1] / 100))) - offset_y) * ratio + 20);
    });


    ctx.lineWidth = 10;

    ctx.font = '20px serif';

    // round the background strokes to prevent spikes
    ctx.lineJoin = 'round';

    var lens_text = $("#LENS_SELECT option:selected").text()
    var camera_text = $("#SENSOR_SELECT option:selected").text()
    var resolution_text = sd[sensor]['w'] + " x " + sd[sensor]['h'] + " (" + sd[sensor]['p'] + "µm)";
    var size_text = r.w.toFixed(2) + " x " + r.h.toFixed(2) + "mm";
    var diag_text = Math.sqrt((r.w ** 2) + (r.h ** 2)).toFixed(2) + "mm diag";
    var img_c_text = (icd[lens] / sd[sensor]['p'] * 1000).toFixed(0) + "px circle";
    var offset_text = offset_x.toFixed(2) + " x " + offset_y.toFixed(2) + "mm offset";

    ctx.strokeStyle = 'black';
    ctx.fillStyle = 'lightgrey';

    ctx.textAlign = 'left';

    // top left
    ctx.strokeText(lens_text, 25, 40, 500);
    ctx.strokeText(camera_text, 25, 70, 500);
    ctx.fillText(lens_text, 25, 40, 500);
    ctx.fillText(camera_text, 25, 70, 500);


    var x_text = (r.w * ratio) - 25;
    var y_text = (r.h * ratio) - 180;
    var maxWidth = 200;

    ctx.textAlign = 'right';

    // top right
    ctx.strokeText(resolution_text, x_text, 40, maxWidth);
    ctx.strokeText(size_text, x_text, 70, maxWidth);
    ctx.strokeText(diag_text, x_text, 100, maxWidth);
    ctx.fillText(resolution_text, x_text, 40, maxWidth);
    ctx.fillText(size_text, x_text, 70, maxWidth);
    ctx.fillText(diag_text, x_text, 100, maxWidth);

    // bottom right
    ctx.strokeText(img_c_text, x_text, y_text + 130, maxWidth);
    ctx.strokeText(offset_text, x_text, y_text + 160, maxWidth);
    ctx.fillText(img_c_text, x_text, y_text + 130, maxWidth);
    ctx.fillText(offset_text, x_text, y_text + 160, maxWidth);


}
