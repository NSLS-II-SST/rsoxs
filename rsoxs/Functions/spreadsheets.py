from rsoxs_scans.spreadsheets import save_samplesxlsx, load_samplesxlsx
from ..startup import rsoxs_config



def load_sheet(path):
    newbar = load_samplesxlsx(path)
    if isinstance(newbar, list):
        rsoxs_config['bar'] = newbar
        ##rsoxs_config.write()
        print(f'replaced persistent bar with bar loaded from {path}')
        return

def save_sheet(path,name):
    save_samplesxlsx(bar=rsoxs_config['bar'],path=path,name=name)
    return
