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
from loci.formats.meta import MetadataRetrieve;
reader = ImageReader()
omeMeta = MetadataTools.createOMEXMLMetadata()
reader.setMetadataStore(omeMeta)
reader.setId(vsi)
seriesCount = reader.getSeriesCount()
omecsv = file('omeMeta.csv','wt')
readercsv = file('reader.csv','wt')
SeriesMDtxt = file('seriesMD.txt','wt')

SeriesChans = []
print("series count is %d" % (seriesCount))
for i in range(seriesCount):
    reader.setSeries(i)
    ChanSize = reader.getEffectiveSizeC()
    TimeSize = reader.getSizeT()
    ZStackSize = reader.getSizeZ()
    # the thumbnail images created by the VSI have 0 len metadata, the
    # actual images have non-zero len metadata
    # note you can pull out all sorts of keys
    print(reader.getSeriesMetadataValue('Channel name #1'))
    seriesmd = reader.getSeriesMetadata()
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
            Chans.append((channum, reader.getSeriesMetadataValue(chankey)))
        SeriesChans.append((i,copy(Chans)))
    SeriesMDtxt.write(strmd)

print(SeriesChans)    

# I think the easiest thing to do is to send the series out to the
# command line utility in a subprocess, rather than reinvent the
# command line utility here
VSIpath = os.path.dirname(vsi)
VSIbn = os.path.basename(vsi)
for series, chans in SeriesChans:
    for channum,channame in chans:
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

# flush the files I was recording metadata tags and
# method information
# to
SeriesMDtxt.flush()
SeriesMDtxt.close()
[omecsv.write(field+'\n') for field in dir(omeMeta)]
omecsv.flush()
omecsv.close()
[readercsv.write(field+'\n') for field in dir(reader)]
readercsv.flush()
readercsv.close()

# good practice to close the reader objects to prevent memory leaks
reader.close()
