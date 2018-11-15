# This file is originall from https://github.com/jtambasco/gnuplotpy

import os
import time
import shutil as sh
import numpy as np
import subprocess
import re
import tempfile

init_pgfplots_ = False

def _read_line(filename, line_number):
    s = None
    with open(filename, 'r') as fs:
        for i, line in enumerate(fs.readlines()):
            if i == line_number:
                s = line
    return s

class _GnuplotDeletingFile:
    def __init__(self, filename):
        self.name = filename

    def __del__(self):
        os.remove(self.name)

class _GnuplotScriptTemp(_GnuplotDeletingFile):
    def __init__(self, gnuplot_cmds):
        _GnuplotDeletingFile.__init__(self, '.tmp_gnuplot.gpi')
        with open(self.name, 'w') as fs:
            fs.write(gnuplot_cmds)

class _GnuplotDataTemp(_GnuplotDeletingFile):
    def __init__(self, *args):
        _GnuplotDeletingFile.__init__(self, '.tmp_gnuplot_data.dat')
        data = np.array(args).T
        with open(self.name, 'wb') as fs:
            np.savetxt(fs, data, delimiter=',')

class _GnuplotDataZMatrixTemp(_GnuplotDeletingFile):
    def __init__(self, z_matrix):
        _GnuplotDeletingFile.__init__(self, '.tmp_gnuplot_data_z_matrix.dat')
        with open(self.name, 'wb') as fs:
            np.savetxt(fs, z_matrix, '%.3f', delimiter=',')

#def gnuplot( script, args_dict={}, data=[]):
def gnuplot( script, **kwargs ):
    '''
    Call a Gnuplot script, passing it arguments and
    datasets.

    Args:
        script(str): The name of the Gnuplot script or the text
        args_dict(dict): A dictionary of parameters to pass
            to the script.  The `key` is the name of the variable
            that the `item` will be passed to the Gnuplot script
            with.
        data(list): A list of lists containing lists to be plotted.
            The lists can be accessed by plotting the variable
            `data` in the Gnuplot script.  The first list in the
            list of lists corresponds to the first column in data,
            and so on.
    Returns:
        str: The Gnuplot command used to call the script.
    '''

    if os.path.exists( script ):
        with open( script ) as f:
            script = f.read( )

    for k in kwargs:
        v = kwargs[k]
        script = script.replace( '@%s@' % k, v )

    # Find rest of the macros.
    for m in re.findall( r'@\S+?@', script ):
        script = script.replace( m, kwargs.get( m.replace( '@',''), '' ) ) 

    # if first argument is a long string then save the string to current
    # directory before running the command.
    # First escape all char.
    script = script.replace( r'"', r"'" ).replace( ';', '' )
    script = ';'.join( filter(None, script.split( '\n' )) );
    script += ';exit;'
    scriptName = '.gnuplot_script'
    with open( scriptName, 'w' ) as f:
        f.write( script )

    while not os.path.isfile( scriptName ):
        time.sleep( 0.0001 )

    subprocess.Popen( [ 'gnuplot', scriptName ] )
    return True

def nx_draw( graph, program = 'neato', ax = None ):
    """Draw to PNG using graphviz (default = neato).
    """
    import matplotlib.image as mpimg
    import matplotlib.pyplot as plt
    from networkx.drawing.nx_agraph import write_dot

    fh, dotfile = tempfile.mkstemp( )
    pngfile = '%s.png' % dotfile
    write_dot( graph, dotfile )
    if ax is not None:
        subprocess.check_output([ program,  "-Tpng",  dotfile, "-o", pngfile], shell=False)
        if os.path.exists( pngfile ):
            im = mpimg.imread( pngfile )
            ax.imshow( im, interpolation = 'none' )
        else:
            raise UserWarning( 'Failed to draw graph using %s' % program)

def matrix_plot( img, xvec, yvec, ax = None, **kwargs ):
    import matplotlib.pyplot as plt
    if ax is None:
        ax = plt.subplot( 111 )

    img = np.matrix( img )
    nc, nr = img.shape
    im = ax.imshow( img
            , interpolation = kwargs.get( 'interpolation', 'none')
            , aspect = kwargs.get( 'aspect', 'auto' ) 
            , cmap = kwargs.get( 'cmap', 'viridis' )
            )

    # apply ticks and labels
    xticks = kwargs.get( 'xticks', [] )
    yticks = kwargs.get( 'yticks', [] )
    if not xticks:
        nticks = kwargs.get( 'num_xticks', kwargs.get( 'num_ticks', 5) )
        xticks = [(i, xvec[int(i)]) for i in np.linspace(0, len(xvec)-1, nticks)]

    xpos, xlabels = zip(*xticks)
    ax.set_xticks(xpos)
    ax.set_xticklabels( [ r'%s' % x for x in xlabels] )

    if not yticks:
        nticks = kwargs.get( 'num_yticks', kwargs.get( 'num_ticks', 5) )
        yticks = [(i, yvec[int(i)]) for i in np.linspace(0, len(yvec)-1, nticks)]

    ypos, ylabels = zip(*yticks)
    ax.set_yticks(ypos)
    ax.set_yticklabels( [ r'%s' % y for y in ylabels] )

    ax.set_xlabel( kwargs.get( 'xlabel', 'NA' ) )
    ax.set_ylabel( kwargs.get( 'ylabel', 'NA' ) )


    if kwargs.get( 'colorbar', True):
        plt.colorbar( im, ax = ax )
    return im

def init_pgfplots( ):
    global init_pgfplots_
    if init_pgfplots_:
        return 
    import matplotlib as mpl
    # Set matplotlib parameters to make it look like pgfplots
    mpl.use('pgf')
    import matplotlib.pyplot as plt
    mpl.style.use( 'classic' )
    mpl.rcParams['text.latex.preamble'] = [
            r'\usepackage{siunitx},\usepackage{libertine}' 
            ]
    mpl.rcParams['text.usetex'] = True
    mpl.rcParams[ 'text.latex.unicode' ] = True

    # The following settings allow you to select the fonts in math mode.
    mpl.rcParams['mathtext.fontset'] = 'stixsans'
    mpl.rcParams['mathtext.default'] = 'regular'
    ### AXES
    mpl.rcParams['axes.labelsize'] =  'small'
    mpl.rcParams['axes.formatter.use_mathtext'] = True
    mpl.rcParams['axes.formatter.min_exponent'] = 0
    mpl.rcParams['axes.formatter.useoffset'] = True  
    mpl.rcParams['axes.formatter.offset_threshold'] = 4  

    mpl.rcParams['axes.spines.left'] = True 
    mpl.rcParams['axes.spines.bottom'] = True
    mpl.rcParams['axes.spines.top'] = False
    mpl.rcParams['axes.spines.right'] = False

    mpl.rcParams['axes.unicode_minus'] = True 
    mpl.rcParams['axes.autolimit_mode'] = data 
    mpl.rcParams['axes.xmargin' ] = 0.1 
    mpl.rcParams['axes.ymargin' ] = 0.1 

    # TICKS
    # see http://matplotlib.org/api/axis_api.html#matplotlib.axis.Tick
    mpl.rcParams['xtick.labelsize'] = 'small'
    mpl.rcParams['xtick.direction'] = 'inout' 
    mpl.rcParams['ytick.labelsize'] = 'small' 
    mpl.rcParams['ytick.direction'] = 'inout'

    # Legend
    mpl.rcParams['legend.loc']         = 'best'
    mpl.rcParams['legend.frameon']     = False     # if True, draw the legend on a background patch
    mpl.rcParams['legend.framealpha']  = 0         # legend patch transparency
    mpl.rcParams['legend.fancybox']    = True      # if True, use a rounded box for the
    mpl.rcParams['legend.fontsize']    = 'small'
    mpl.rcParams['legend.borderpad']   = 0
    init_pgfplots_ = True

def pgfplots( x, y, ax, df=None, **kwargs):
    """Plot normal x-y curve like with pdfplots like settings.
    Also put valus into a dataframe and return it so it can be saved into a csv
    file.
    """
    init_pgfplots()
    import pandas
    if df is None:
        df = pandas.DataFrame()

    ax.plot( x, y, **kwargs)
    if kwargs.get('label', ''):
        ax.legend()

    if kwargs.get('xlabel', ''):
        ax.set_xlabel( kwargs['xlabel'] )
        df[kwargs['xlabel']] =  x
    if kwargs.get('ylabel', ''):
        ax.set_ylabel( kwargs['ylabel'] )
        df[kwargs['ylabel']] =  y
    if kwargs.get('title', '' ):
        ax.set_title( kwargs.get('title', '' ) )

    return df
