#! /usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Wed Jul  8 09:39:28 2015

@author: niko
"""


import argparse
import os
import glob
import sys
import shutil

# ========================================================================
# ========================================================================
# ========================================================================

if __name__ == '__main__':

  parser = argparse.ArgumentParser(description='Process command line parameters.')
  parser.add_argument('--src', default='.', help='The src directory of the existing paper.')
  parser.add_argument('--dst', default='.', help='The arXiv ready files will be put here')
  parser.add_argument('--main', help='The main latex file')
  parser.add_argument('--zip', default='arxiv.zip', help='The name of the zip file that is created')

  args = parser.parse_args()


  # create the directories at the destination
  print 'Creating output directory at', args.dst
  dst_path = os.path.join(args.dst, 'arxiv-src')

  if not os.path.exists(dst_path):
    try:
      os.makedirs(dst_path)
    except Exception,e:
      print e
      print "Could not create", dst_path, "\nStopping."
      sys.exit()


  # first identify all .tex files
  pattern = os.path.join(args.src, '*','*.tex')
  tex_files = glob.glob(pattern)
  pattern = os.path.join(args.src, '*.tex')
  tex_files.extend(glob.glob(pattern))


  # if there is a main.tex file, that is the main file
  # if there is only one tex file, that is the main file
  # if there are more, we need a little help
  # if there is a .latexmain this also tells us the main file
  print tex_files
  main_files = [f for f in tex_files if f.endswith('main.tex')]
  if len(main_files) == 1:
      tex_main_file = main_files[0]
  elif len(tex_files) == 1:
    tex_main_file = tex_files[0]
  elif args.main:
    tex_main_file = os.path.join(args.src, args.main.split('/')[-1])
  else:
    pattern = os.path.join(args.src, '*.latexmain')
    tex_main_files = glob.glob(pattern)
    if len(tex_main_files)==1:
      tex_main_file = tex_main_files[0].split('.latexmain')[0]
      shutil.copy(tex_main_files[0], dst_path)
    else:
      print "Error, could not determine the main latex file. Please use option --main"
      sys.exit()

  try:
    shutil.copyfile(tex_main_file, os.path.join(dst_path, tex_main_file.split('/')[-1]))
  except Exception,e:
    print e

  print '=== Using main LaTeX file', tex_main_file

  # go through the main file, look for included latex and bibtex files
  tex_files = []
  tex = file(tex_main_file,'r')
  print '=== Looking for included input files in main LaTeX fike', tex_main_file, '==='
  for line in tex:
    if '\input' in line and not line.strip().startswith('%'):
      fn = line.split('\input{')[1].split('}')[0]
      fn = os.path.normpath(os.path.join(args.src, fn))
      print '\tFound input file', fn
      if not fn.endswith('.tex') and not fn.endswith('.tikz'):
        fn=fn+'.tex'
      tex_files.append(fn)

      try:
        shutil.copyfile(fn, os.path.join(dst_path, fn.split('/')[-1]))
      except Exception,e:
          print e

    elif 'bibliography{' in line and not line.strip().startswith('%'):
      fns = line.split('bibliography{')[1].split('}')[0]
      for fn in fns.split(','):
          fn = os.path.normpath(os.path.join(args.src, fn))
          if not fn.endswith('.bib'):
            fn = fn +'.bib'
          print '\tFound bibtex file', fn
          try:
            shutil.copyfile(fn, os.path.join(dst_path, fn.split('/')[-1]))
          except Exception,e:
              print e


  tex_files.append(tex_main_file)
  print
  print

  # parse tex files, finding all needed figure files and copy them to our destination
  img_files = []
  graphicspath = ''
  for f in tex_files:
    print '=== Looking for figures in LaTeX file', f, '==='
    tex = file(f, 'r')
    for line in tex:
      if '\graphicspath' in line and not line.strip().startswith('%'):
        graphicspath = line.split('{')[-1].split('}')[0]
        print '\tFound graphicspath', graphicspath

      if '\includegraphics' in line and not line.strip().startswith('%'):
        figure = line.split('{')[1].split('}')[0]
        print '\tFound figure file', figure

        path = figure.split('/')[:-1]
        if path == [] or path[-1] != graphicspath.strip('/'):
          figure_prefix = graphicspath
        else:
          figure_prefix = ''

        full_path = os.path.join(dst_path, *path)
        if not os.path.exists(full_path):
          os.makedirs(full_path)

        # copy it
        try:
          shutil.copyfile(os.path.join(args.src, figure_prefix, figure), os.path.join(dst_path, figure))
        except Exception,e:
          print e

  print
  print

  # for each tex file remove the outcommented and empty lines using sed
  print '=== removing outcommented and empty lines in LaTeX files ==='
  for fn in tex_files:
    fn = os.path.join(dst_path, fn.split('/')[-1])
    print fn

    cmd = "sed -i '/^\s*%/d' " + fn
    os.system(cmd)

    # cmd = "sed -i '/^\s*$/d' " + fn
    # os.system(cmd)


  print
  print


  # find style templates
  print '=== Looking for style templates ==='
  pattern = os.path.join(args.src, '*.cls')
  style_files = glob.glob(pattern)
  pattern = os.path.join(args.src, '*.bst')
  style_files.extend(glob.glob(pattern))
  pattern = os.path.join(args.src, '*.sty')
  style_files.extend(glob.glob(pattern))

  for fn in style_files:
    print '\t Found',fn
    shutil.copy(fn, dst_path)

  print
  print





  # go through the main file again and change the input paths to the dst dir
  main = file(os.path.join(dst_path, tex_main_file.split('/')[-1]),'r')
  main_copy= file(os.path.join(dst_path, tex_main_file.split('/')[-1]) + '.new','w')
  for line in main:
    if '\input' in line:
      fn = line.split('\input{')[1].split('}')[0]
      fn = fn.split('/')[-1]
      print fn
      l = '\input{'+fn+'}\n'
      main_copy.write(l)
    elif 'bibliography{' in line:
      fns = line.split('bibliography{')[1].split('}')[0]
      bibs = [x.split('/')[-1] for x in line.split('bibliography{')[1].split('}')[0].split(',')]
    #   for fn in fns.split(','):
    #       fn = fn.split('/')[-1]
    #       bibs += fn
    #       print fn
      print bibs
      l = '\\bibliography{'+','.join(bibs)+'}\n'
      main_copy.write(l)
    else:
      main_copy.write(line)

  main_copy.close()
  main.close()

  shutil.move(os.path.join(dst_path, tex_main_file.split('/')[-1]) + '.new', os.path.join(dst_path, tex_main_file.split('/')[-1]), )


  # ZIP the whole directory
  print
  print

  cwd = os.getcwd()
  print '=== Creating archive arxiv.zip ==='
  cmd = 'cd %s; zip -r %s/%s * ; cd %s' % (dst_path, cwd, args.zip, cwd)
  # cmd = 'cd ' + dst_path + '; zip -r ' + args.zip + ' * ; cd '
  print cmd
  os.system(cmd)


  print
  print

  # compile and bibtex the project
  print '=== attempting to compile and bibtex LaTeX sources ==='
  try:
     fn = tex_main_file.split('/')[-1].split('.')[0]
     cmd = 'cd %s;' % dst_path
     cmd += 'pdflatex --interaction nonstopmode %s;' % fn
     cmd += 'bibtex %s' % fn
     os.system(cmd)
  except:
     print '!!! Error generating .bbl file. Literature references will not work on arxiv. Please provide .bbl file manually.'

  print '=== looking for bibtex files ==='
  pattern = os.path.join(args.src, '*.bbl')
  bibtex_files = glob.glob(pattern)
  for fn in bibtex_files:
    print '\t Found',fn
    shutil.copy(fn, dst_path)

  # add the resulting .bbl file to the zip archive
  print
  print
  print '=== Updating arxiv.zip ==='
  cwd = os.getcwd()
  fn = tex_main_file.split('/')[-1].split('.')[0]
  cmd = 'cd %s; zip -u %s/%s %s' % (dst_path, cwd, args.zip, fn+'.bbl')
  print cmd
  os.system(cmd)
