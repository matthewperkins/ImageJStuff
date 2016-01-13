import sys, os
import subprocess
from copy import copy
# load an example vsi file
vsi = os.path.join(os.environ.get("HOME"),
                   'Documents',
                   'alberini',
                   'VS100',
                   'RA2015_11_19',
                   'cfos',
                   'IGF2_01',
                   'IGF2_01_cfos_1of2_01.vsi')

# parse metadata
from loci.formats import ImageReader
from loci.formats import MetadataTools
from loci.formats.out import TiffWriter
from loci.formats.meta import MetadataRetrieve

def findImageSeries(vsi_reader):
    '''return a list of tuples 

        [(SeriesNum, [(ChanNum, ChanName), (ChanNum, ChanName)]) 
         (SeriesNum, [(ChanNum, ChanName), (ChanNum, ChanName)]), ... ]

       of the series that contain actual images an not thumbnails from VS120 pictures'''
    SeriesChans = []
    seriesCount = vsi_reader.getSeriesCount()
    print("series count is %d" % (seriesCount))
    for i in range(seriesCount):
        vsi_reader.setSeries(i)
        ChanSize = vsi_reader.getEffectiveSizeC()
        TimeSize = vsi_reader.getSizeT()
        ZStackSize = vsi_reader.getSizeZ()
        # the thumbnail images created by the VSI have 0 len metadata, the
        # actual images have non-zero len metadata
        # note you can pull out all sorts of keys
        print(vsi_reader.getSeriesMetadataValue('Channel name #1'))
        seriesmd = vsi_reader.getSeriesMetadata()
        strmd = seriesmd.toString()
        mdlen = len(seriesmd)
        if mdlen==0:
            print("S:%d is fake series, metadata len = 0!" % (i))
        else:
            print("S:%d REAL, metadata len = %d" % (i, mdlen))
            print("S:%d has %d channels, "\
                  "%d time snaps, %d ZStacks" % (i,
                                                 ChanSize,
                                                 TimeSize,
                                                 ZStackSize))
            Chans = []
            for channum in range(ChanSize):
                chankey = "Channel name #%d" % (channum+1)
                Chans.append((channum, vsi_reader.getSeriesMetadataValue(chankey)))
            SeriesChans.append((i,copy(Chans)))
    return(SeriesChans)

def SubProcessConvert(vsi_path, vsi_reader, SeriesChans):
    # I think the easiest thing to do is to send the series out to the
    # command line utility in a subprocess, rather than reinvent the
    # command line utility here
    VSIpath = os.path.dirname(vsi_path)
    VSIbn = os.path.basename(vsi_path)
    for series, chans in SeriesChans:
        for channum,channame in chans:
            tifs_dir = os.path.join(VSIpath, 'tifs')
            if not os.path.exists(tifs_dir): os.mkdir(tifs_dir)
            tifname = VSIbn.split(os.path.extsep)[0]+\
            "_S_%d_C_%d_%s.tif" % (series, channum, channame)
            frmtd_call = ['bfconvert',
                          '-compression',
                          'LZW',
                          '-series',
                          "%d" % series,
                          '-channel',
                          "%d" % (channum),
                          "%s" % (vsi),
                          os.path.join(VSIpath,'tifs',tifname)]
            print(frmtd_call)
            subprocess.call(frmtd_call)

def initreader(vsi_path):
    reader = ImageReader()
    omeMeta = MetadataTools.createOMEXMLMetadata()
    reader.setMetadataStore(omeMeta)
    reader.setId(vsi_path)
    return(reader)

if __name__=='__main__':
    for root, dirs, files in os.walk('.'):
        for vsi in filter(lambda f: f.endswith(".vsi"), files):
            vsi_reader = initreader(os.path.join(root, vsi))
            SeriesChans = findImageSeries(vsi_reader)
            SubProcessConvert(os.path.join(root,vsi), vsi_reader, SeriesChans)
            # good practice to close the reader objects to prevent memory leaks
            vsi_reader.close()
