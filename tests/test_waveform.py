"""Critical waveform properties: both channels, peak retention and source changes."""
import numpy as np
import soundfile as sf
from dx_studio.waveform import peaks,cached_peaks


def test_peaks_preserve_transients_and_opposite_stereo_channels(tmp_path):
    path=tmp_path/'mix.wav';data=np.zeros((1600,2));data[400]=[.8,-.8]
    sf.write(path,data,16000,subtype='FLOAT')
    result=peaks(path,16)
    assert result['duration']==.1 and result['sample_rate']==16000
    assert max(result['peaks'])==.8 and len(result['peaks'])==16


def test_cache_rebuilds_for_changed_audio_and_missing_mix_is_not_an_error(tmp_path):
    path=tmp_path/'mix.wav'
    assert not cached_peaks(path)['ready']
    sf.write(path,np.zeros(1600),16000,subtype='FLOAT');first=cached_peaks(path)
    assert cached_peaks(path)==first
    sf.write(path,np.ones(3200)*.5,16000,subtype='FLOAT');second=cached_peaks(path)
    assert first['key']!=second['key'] and second['duration']==.2
    assert max(second['peaks'])==.5
