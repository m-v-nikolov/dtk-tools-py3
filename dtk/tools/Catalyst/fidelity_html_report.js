function populateSections(){
    h2s = document.getElementsByTagName('h2')
    scs = document.getElementById('sections')
    if(scs != null && scs.options != null)for(j=0; j < scs.options.length; j++)scs.remove(0)
    for(i = 0; i < h2s.length; i ++){
        if(h2s[i].innerHTML.indexOf('Fidelity Report:') == -1){
            var option = document.createElement("option");
            option.text = h2s[i].innerHTML;
            scs.add(option);
        }
    }
}

function scrollToSection(name){
    h2s = document.getElementsByTagName('h2')
    for(i = 0; i < h2s.length; i ++){
        if(h2s[i].innerHTML == name){
            h2s[i].scrollIntoView()
            window.scrollBy(0, -150)
            break;
        }
    }
}

function switchCompareModeImages(ch){

    sweeps = document.getElementById('cp_w_base_means_switch')
    runs = document.getElementById('cp_w_base_means_runs_switch')
    sweep_value = sweeps.options[sweeps.selectedIndex].value
    run_value = runs.options[runs.selectedIndex].value

    imgs = getImages('_time_series_rolling.png')
    ends = (imgs.length > 0 ? '_time_series_rolling.png' : '_time_series.png')

    imgs = getImages('_time_series')
    for(i = 0; i < imgs.length; i ++){
        var filename = getFileName(imgs[i].src)
        if(filename.indexOf('zoom_to_end') != -1) continue
        // ends with
        if( filename.indexOf(ends, filename.length - ends.length) !== -1 && (sweep_value == 'show_all' || filename.indexOf('_sw'+sweep_value+'_') !== -1) && filename.indexOf('_rn'+run_value+'_') !== -1){
            imgs[i].style.display = ''
        }else{
            imgs[i].style.display = 'none'
        }
    }
}

function toggleRollingImages(){
    imgs = getImages('_time_series_rolling.png')
    if(imgs.length > 0){
        btn = document.getElementById('img_rolling_switch')
        btn.innerHTML = 'Show Rolling-Mean Plots'
        replaceImages(imgs, '_time_series_rolling.png', '_time_series.png')
    }else{
        imgs = getImages('_time_series.png')
        if(imgs.length > 0){
            btn = document.getElementById('img_rolling_switch')
            btn.innerHTML = 'Show Raw Data Plots'
            replaceImages(imgs, '_time_series.png', '_time_series_rolling.png')
        }
    }
}
function getImages(find_str){
    imgs = document.getElementsByTagName('img')
    found = []
    for(i = 0; i < imgs.length; i ++){
        var filename = getFileName(imgs[i].src)
        if(filename.indexOf(find_str) !== -1){
            found.push(imgs[i])
        }
    }

    return found
}
function replaceImages(imgs, replace_str, with_str){
    for(i = 0; i < imgs.length; i ++){
        var dir_path = getDirPath(imgs[i].src)
        var filename = getFileName(imgs[i].src)
        filename = filename.replace(replace_str, with_str)
        imgs[i].src = dir_path + filename
    }
}

function toggleReportHeader(btn){
    hdr = document.getElementById('report_header')
    hdr_ph = document.getElementById('report_header_ph')

    if(hdr.style.display.replace('inline', '') == ''){
        btn.innerHTML = '+'
        hdr.style.display = 'none'
        hdr_ph.style.display = 'none'
    }else{
        btn.innerHTML = '-'
        hdr.style.display = ''
        hdr_ph.style.display = ''
    }
}

function getDirPath(file_path){
    var filename = getFileName(file_path)
    return file_path.substring(0, file_path.length - filename.length);
}

function getFileName(file_path){
    return file_path.replace(/^.*[\\\/]/, '')
}

function initPage(){
    populateSections()
}