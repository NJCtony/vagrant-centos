function isApiUrl() {
  var url = window.location.toString();
  if (url.search('api') >= 0) {
    return true;
  }
  return false;
}

function rgbToString(value_list, opacity) {
  return 'rgba(' + value_list[0].toString() + ',' + value_list[1].toString() + ',' + value_list[2].toString() + ',' + opacity.toString() + ')';
}
