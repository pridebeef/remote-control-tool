'use strict';

// return form data for given element ids
const collect_settings = (element_ids) =>
	element_ids.reduce(
		(acc, e) => ({ ...acc, [e]: document.getElementById(e).value }),
		{}
	);

const get_checkbox = (checkbox) => document.getElementById(checkbox).checked;

const get_radio = (name) =>
	Array.from(document.getElementsByName(name)).find((i) => i.checked).value;

const formdata_from_settings = (settings) => {
	let formdata = new FormData();
	Object.keys(settings).forEach((key) => formdata.append(key, settings[key]));
	return formdata;
};

const post_data = (formdata) => {
	console.log(window.location.href + 'send');
	fetch(window.location.href + 'send', { method: 'POST', body: formdata });
};

function send_open_url() {
	var settings = collect_settings(['ip', 'port', 'url', 'password']);
	let formdata = formdata_from_settings(settings);
	formdata.append('command', 'open_url');
	formdata.append('autoplay', get_checkbox('autoplay'));
	formdata.append('fullscreen', get_checkbox('fullscreen'));
	post_data(formdata);
}

function send_wearable() {
	var settings = collect_settings(['ip', 'port', 'password']);
	let formdata = formdata_from_settings(settings);
	formdata.append('command', 'wearable');
	formdata.append('mode', get_radio('mode'));
	post_data(formdata);
}
