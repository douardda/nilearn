# -*- coding: utf-8 -*-
"""

"""
import os, os.path as osp
import sys
import shutil
import collections
import json
import threading
import time

import nibabel

from nilearn import datasets
from nilearn.plotting import plot_stat_map, plot_glass_brain
from nilearn.decomposition.canica import CanICA

from externals.formlayout.formlayout import fedit, QApplication

from externals import tempita

import report_api as api
from .reportviewer import ReportViewer, ComputationProgressViewer

TEMPLATES = osp.join(osp.dirname(__file__), 'templates')
REPORT = osp.join(TEMPLATES, 'report')

def chose_params():
    datalist = [('n_components', 20),
                ('smoothing_fwhm', 6.),
                ('threshold', 3.),
                ('verbose', ['10', '0', '10']),
                ('input_folder', '%folder_picker')
                ]

    adict = collections.OrderedDict(datalist)

    result = fedit(datalist, title="CanICA",
                   comment="Enter the CanICA parameters")

    if result:
        params = dict(zip(adict.keys(), result))
        params['verbose'] = int(params['verbose'])
        print 'params: ', params
        return params

def get_fitted_canica(func_files, **params):
    input_folder = params.pop('input_folder')
    func_files = sorted(os.path.join(root, filename)
                        for root, dirs, filenames in os.walk(input_folder)
                        for filename in filenames if filename.endswith('.nii.gz'))

    canica = CanICA(memory='nilearn_cache', memory_level=5, random_state=0,
                    n_jobs=-1, **params)


    if not func_files:
        raise ValueError('Could not find any files in the input folder')
    canica.fit(func_files)
    return canica


def generate_images(components_img, n_components, images_dir, glass=False):
    # Remove existing images
    if os.path.exists(images_dir):
        shutil.rmtree(images_dir)
    os.makedirs(images_dir)
    output_filenames = [osp.join(images_dir, 'IC_{}.png'.format(i))
                        for i in range(n_components)]
        

    for i, output_file in enumerate(output_filenames):
        plot_stat_map(nibabel.Nifti1Image(components_img.get_data()[..., i],
                                          components_img.get_affine()),
                      display_mode="z", title="IC %d" % i, cut_coords=7,
                      colorbar=False, output_file=output_file)
    if glass:
        output_filenames = [osp.join(images_dir, 'glass_IC_{}.png'.format(i))
                            for i in range(n_components)]
        for i, output_file in enumerate(output_filenames):
            plot_glass_brain(nibabel.Nifti1Image(components_img.get_data()[..., i],
                                                 components_img.get_affine()),
                             display_mode="ortho", title="IC %d" % i,
                             output_file=output_file)



def generate_report(params_dict, img_src_filenames):
    report = api.Report()

    report.add(api.Section('Model parameters'),
               api.Table(params_dict.iteritems(),
                         headers=('Parameter', 'Value')))


    for counter, filename in enumerate(img_src_filenames):
        caption = 'component {}'.format(counter)
        section = api.Section('Component #{}'.format(counter))
        #section.add(
        #    api.Paragraph('This is some paragraph text related to '
        #                  'component #{}'.format(counter))
        #    )
        section.add(
            api.Image(filename, caption=caption)
            )
        report.add(section)
    report.add(api.Section('About').add(api.Paragraph('This report has been generated using the nilearn toolkit.')))
    report.add(api.Section('Contact').add(api.Paragraph('See <a href="https://github.com/nilearn/nilearn/">https://github.com/nilearn/nilearn/</a>')))

    return report


def prepare_report_directory(directory):
    if osp.exists(directory):
        shutil.rmtree(directory)
    shutil.copytree(REPORT, directory)


def run(func_files, params, output_dir):
    canica = get_fitted_canica(func_files, **params)
    # Retrieve the independent components in brain space
    components_img = canica.masker_.inverse_transform(canica.components_)
    generate_images(components_img, params['n_components'],
                    osp.join(output_dir, 'images'),
                    glass=True)
    json.dump(params, open(osp.join(output_dir, 'params.json'), 'w'))



def main():

    import argparse

    parser = argparse.ArgumentParser(description='Run a CanICA computation and produce an HTML report')
    parser.add_argument('-r', '--report-only', default=False, action='store_true',
                        help='regenerate the report from an existing comuputation')
    parser.add_argument('-o', '--output', default='report', metavar='DIRECTORY',
                        help='directory in which to write the result files and reports',)

    args = parser.parse_args()

    dataset = datasets.fetch_adhd()
    func_files = dataset.func

    app = QApplication(sys.argv)

    output_dir = osp.abspath(args.output)

    params_file = osp.join(output_dir, 'params.json')
    if args.report_only:
        params = json.load(open(params_file))
    else:
        prepare_report_directory(output_dir)

        params = chose_params()
        if params:
            stdout, stderr = sys.stdout, sys.stderr
            try:
                dlg = ComputationProgressViewer()
                sys.stdout = dlg
                sys.stderr = dlg
                compute_thread = threading.Thread(target=run,
                                                  args=(func_files, params, output_dir))
                dlg.show()
                compute_thread.start()
                while compute_thread.isAlive():
                    app.processEvents()
                    time.sleep(0.3)
                compute_thread.join()
            finally:
                sys.stdout, sys.stderr = stdout, stderr
            json.dump(params, open(osp.join(output_dir, 'params.json'), 'w'))

    if params:
        img_src_filenames = [osp.join(output_dir, 'images', fname)
                             for fname in os.listdir(osp.join(output_dir, 'images'))
                             if fname.startswith('IC_')]
        report = generate_report(params, img_src_filenames)
        reportindex = osp.abspath(osp.join(output_dir, 'index.html'))
        report.save_html(reportindex)

        viewer = ReportViewer('file://{}'.format(reportindex))
        viewer.show()
        viewer.exec_()


if __name__ == '__main__':
    main()
