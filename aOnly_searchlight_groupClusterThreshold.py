def load_attributes(attr_file):
    x = os.path.join(attr_file)
    attr = ColumnData(x, header=True)
    # attr = SampleAttributes(x)
    return attr
def load_Anii(nii_file, mask_file, attr):
    """load experiment dataset"""
    fds = fmri_dataset(samples=os.path.join(nii_file),
                       targets=attr.Alabel, chunks=attr.run,
                       mask=os.path.join(mask_file))
    return fds
def lag_correction(fds, runTRs, lagTRs):
    """correct dataset for hemodynamic lag"""
    # split dataset into runs
    nRuns = len(fds) / float(runTRs)
    if int(nRuns) != nRuns:
        print 'Error! number of TRs per run must be a factor of total TRs'
        raise SystemExit
    nRuns = int(nRuns)
    split_fds = []
    for i in range(nRuns):  # split dataset into separate runs
        split_fds.append(fds[i * runTRs:(i + 1) * runTRs])
    # do the shift for each run
    for i in range(len(split_fds)):
        split_fds[i].sa.targets[lagTRs:] = \
            split_fds[i].sa.targets[:-lagTRs]  # need to shift target labels too

        split_fds[i].sa.censor[lagTRs:] = (split_fds[i]
                                               .sa.censor[:-lagTRs])  # and censor labels

        split_fds[i].sa.cond[lagTRs:] = \
            split_fds[i].sa.cond[:-lagTRs]  # and cond label

        split_fds[i].sa.trial[lagTRs:] = \
            split_fds[i].sa.trial[:-lagTRs]  # and trial label

        split_fds[i].sa.chunks[lagTRs:] = \
            split_fds[i].sa.chunks[:-lagTRs]  # and run label

        split_fds[i].sa.SN[lagTRs:] = \
            split_fds[i].sa.SN[:-lagTRs]  # and run label


        split_fds[i] = (split_fds[i])[lagTRs:]

    ##  merge back datasets
    fds = split_fds[0]
    for i in range(1, len(split_fds)):
        fds.append(split_fds[i])

    return fds

# libraries needed by pymvpa
import os
import sys
from mvpa2.suite import *
import numpy as np
import matplotlib as plt

# a few more settings for searchlight
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
mvpa2.debug.active = ['APERM', 'SLC']

# subject info.
sName = ["01LES", "02LJA", "03HJJ", "04HJH", "05YYH", "06YJG", "07CES", "08LKY", "09JHY", "10LIY", "11KDB", "12NJS",
         "13NHJ", "14JJY"]
nsbj = 1 #len(sName)
xSN_range =13

# experiment info.
cond = ["aOnly"]
if len(cond) == 1:
    xCond = 0
nRun = 10
nTR = 66

# decoding parameters
useTR = 4
lagTR = 2
nTarget = 2  # the number of testing lines
chance_level = 0.5

# permutation parameters
nPerm = 100


for xSN in range(xSN_range, xSN_range+1):

    #path
    basedir = '/sas2/PECON/HJY/CrM/Exp1'
    os.chdir(basedir)
    subj_path = os.path.abspath('%(subj)s/Normalization/Searchlight_%(subj)s' % {"subj": sName[xSN]})
    attr_path = os.path.abspath('%(subj)s/BH_data/onset' % {"subj": sName[xSN]})
    roi_path = '/sas2/PECON/HJY/CrM/Exp2/groupAnalysis'
    #roiDir = os.path.abspath('ROImasks')
    slc_path='/sas2/PECON/HJY/CrM/Exp1/groupAnalysis/aOnly/Searchlight_7radius'
    tmp_path=slc_path + '/tmp'

    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)
    if not os.path.exists(slc_path):
        os.makedirs(slc_path)

    #file to be loaded
    nii = 'aOnly@MNI_FNL.nii'
    ROI = ["Mask_MNI"]  # mask
    datFile = '%(path)s/%(subj)s%(nii_name)s' % {"path": subj_path, "subj": sName[xSN], "nii_name": nii}
    mask = '%(path)s/%(roi)s.nii' % {"path": roi_path, "roi": ROI[0]}
    attrFile = '%(path)s/%(subj)s_aOnlybasicOnset.txt' % {"path": attr_path, "subj": sName[xSN]}

    # FNL files to be made
    sl_perm_nii_name = '%s_sl_permFNL.nii' % cond[xCond]
    sl_perm_npy_name = '%s_sl_permFNL.npy' %cond[xCond]
    sl_file_name='%s_sl_7radiusFNL.nii' %cond[xCond]
    sl_result = '%(path)s/%(subj)s%(file)s' % {"path": slc_path, "subj": sName[xSN], "file": sl_perm_nii_name}
    sl_perm_subj_npy_file = '%(path)s/%(subj)s%(file)s' % {"path": slc_path, "subj": sName[xSN], "file": sl_perm_npy_name}
    sl_result_name = '%(path)s/%(subj)s%(file)s' % {"path": subj_path, "subj": sName[xSN], "file": sl_file_name}

    # tmp files to be made
    tmp_sl_perm_nii_name = '%s_sl_perm.nii' % cond[xCond]
    tmp_sl_perm_npy_name = '%s_sl_perm.npy' % cond[xCond]
    tmp_perm_subj_nii_file='%(path)s/tmp.%(subj)s%(nii_name)s' % \
                           {"path": tmp_path, "subj": sName[xSN], "nii_name": tmp_sl_perm_nii_name}
    tmp_perm_subj_npy_file='%(path)s/tmp.%(subj)s%(nii_name)s' % \
                           {"path": tmp_path, "subj": sName[xSN], "nii_name": tmp_sl_perm_npy_name}

    # load stimulus files
    attr = load_attributes(attr_file=attrFile)

    # load nii
    fds = load_Anii(nii_file=datFile, mask_file=mask, attr=attr)
    fds.sa['censor'] = attr.censor
    fds.sa['cond'] = attr.cond
    fds.sa['trial'] = attr.trial
    fds.sa['TR'] = attr.TR
    fds.sa['SN'] = np.full((fds.shape[0],), 1)*(xSN+1)

    # know your data shape
    vox=fds.shape[1]
    print "# of voxels in MNI space: %d" % fds.shape[1]

    ####### bit of preprocessing ########
    fds.samples = asarray(fds.samples)
    fds = lag_correction(fds=fds, runTRs=nTR, lagTRs=lagTR)  # another custom subfunction
    afterlagN = len(fds)
    print "After lag correction: %d " % afterlagN
    ## remove censored points (motion and outlier)
    fds = fds[fds.sa.censor == 1]
    print "Censored points: %d " % (afterlagN - len(fds))
    ## remove oddball trials
    fds = fds[fds.sa.cond != 4]
    ## remove 'rest' TRs
    fds = fds[fds.targets != 0]

    fds_cond = fds.copy(deep=True)
    ## zscore before removing rest TRs
    zscore(fds_cond, chunks_attr='chunks')

    ## get a dataset with one sample per stimulus category for each run
    averager = mean_group_sample(['targets', 'chunks'])
    fds_cond = fds_cond.get_mapped(averager)

    clf = LinearCSVMC()
    partitioner = ChainNode([NFoldPartitioner(cvtype=1),
                             Balancer(attr='targets',
                                      count=1,
                                      limit='partitions',
                                      apply_selection=True)],
                            space='partitions')
    permutator = AttributePermutator('targets', count=nPerm)
    cv_mc = CrossValidation(clf,
                            partitioner,
                            errorfx=mean_match_accuracy,
                            postproc=mean_sample(),
                            enable_ca=['stats'])
    sl_mc = sphere_searchlight(cv_mc,
                               radius=7,
                               space='voxel_indices',
                               nblocks=400,
                               nproc=4,
                               postproc=mean_sample()
                               )
    ds = fds_cond.copy(deep=False,
                       sa=['targets', 'chunks'],
                       fa=['voxel_indices'],
                       a=['mapper'])
    ds.samples = np.nan_to_num(ds.samples)

    sl_map_7radius = sl_mc(ds)

    print "Saving results..."
    nimg = map2nifti(fds, data=sl_map_7radius)
    nimg.to_filename(sl_result_name)


    print "start searchlight perm.: %s" % sName[xSN]

    #array for concat.
    SN_perm_array = np.array([]).reshape((0,vox))
    sl_map = []
    for i in permutator.generate(ds):
        sl_map.append(sl_mc(i))
        #save tmp. files
        tmp_perm = vstack(sl_map, a=0)
        tmp_nifti = map2nifti(fds, data=tmp_perm)
        tmp_nifti.to_filename(tmp_perm_subj_nii_file)
        SN_perm_array = np.asarray(tmp_perm.samples)
        np.save(tmp_perm_subj_npy_file, SN_perm_array)

    print "%s's %dth permutation finished!" % (sName[xSN], nPerm)
    sl_map_perm = vstack(sl_map, a=0)
    fnl_nifti = map2nifti(fds, data=sl_map_perm)
    fnl_nifti.to_filename(sl_result)
    np.save(sl_perm_subj_npy_file, sl_map_perm.samples)


#after each sub's permutation
#Statistical evaluation of group-level average accuracy maps

import mvpa2.algorithms.group_clusterthr as gct
import scipy.sparse as sp

mvpa2.debug.active = ['GCTHR']

# subject info.
sName = ["01LES", "02LJA", "03HJJ", "04HJH", "05YYH", "06YJG", "07CES", "08LKY", "09JHY", "10LIY", "11KDB", "12NJS",
         "13NHJ"]
# load nii
sl_all = []
sl_sub = []
perm_chunk = np.array([]).reshape((0,1))
for xSN in sub:

    basedir = '/sas2/PECON/HJY/CrM/Exp1'
    os.chdir(basedir)
    subj_path = os.path.abspath('%(subj)s/Normalization/Searchlight_%(subj)s' % {"subj": sName[xSN]})
    attr_path = os.path.abspath('%(subj)s/BH_data/onset' % {"subj": sName[xSN]})
    roi_path = '/sas2/PECON/HJY/CrM/Exp2/groupAnalysis'
    #roiDir = os.path.abspath('ROImasks')
    slc_path='/sas2/PECON/HJY/CrM/Exp1/groupAnalysis/aOnly/Searchlight'
    slc_path2='/sas2/PECON/HJY/CrM/Exp1/groupAnalysis/aOnly/Searchlight/FNL'
    if not os.path.exists(slc_path2):
        os.makedirs(slc_path2)

    tmp_path=slc_path + '/tmp'

    #file to be loaded
    nii = 'aOnly@MNI_FNL.nii'
    ROI = ["Mask_MNI"]  # mask
    datFile = '%(path)s/%(subj)s%(nii_name)s' % {"path": tmp_path, "subj": sName[xSN], "nii_name": nii}
    mask = '%(path)s/%(roi)s.nii' % {"path": roi_path, "roi": ROI[0]}
    attrFile = '%(path)s/%(subj)s_aOnlybasicOnset.txt' % {"path": attr_path, "subj": sName[xSN]}
    sl_result = '%(path)s/%(subj)s%(file)s' % {"path": slc_path, "subj": sName[xSN], "file": sl_perm_nii_name}

    #append
    fds = fmri_dataset(samples=sl_result, mask=mask)
    new_chunk = np.full(nPerm,1)*(xSN+1)
    fds.sa['SN'] = new_chunk

    sl_all.append(fds)

sl_all_map = vstack(sl_all, a=0)


sl_real = []
real_chunk = np.zeros((len(sName), 1))
#load real data
for xSN in sub:

    subj_path = os.path.abspath('%(subj)s/Normalization/Searchlight_%(subj)s' % {"subj": sName[xSN]})

    #real data
    real_sl_nii_name = '_sl.nii.gz'
    real_subj_nii_file = '%(path)s/%(subj)s%(nii_name)s' % {"path": subj_path, "subj": sName[xSN], "nii_name": real_sl_nii_name}

    fds = fmri_dataset(samples=real_subj_nii_file, mask=mask)
    fds.sa['SN'] = np.full(1,1)*(xSN+1)
    sl_mean = np.mean(fds.samples)
    sl_std = np.std(fds.samples)
    print "%s Searchlight results: mean accuracy %2.3f, std %2.3f" % (sName[xSN], sl_mean, sl_std)
    sl_real.append(fds)

sl_real_map = vstack(sl_real, a=0)
# avgr = mean_sample()
# sl_real_map_mean = avgr(sl_real_map)

sl_all_map.fa['voxel_indices'] = sl_real_map.fa['voxel_indices']

#bootstrap, find the per-feature threshold that corresponds to some p
clthr = gct.GroupClusterThreshold(n_bootstrap = 100000,
                                  feature_thresh_prob=0.001,
                                  chunk_attr='SN',
                                  fwe_rate=0.05,
                                  multicomp_correction='fdr_bh',
                                  n_blocks=800, n_proc=4)

print('bootstrapping...')
clthr.train(sl_all_map) #bootstrapping group-level chance map
print('Estimate significance & threshold the results... ')
res = clthr(sl_real_map)

#compute p-values for specific sized clusters
clustr_area = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20])
#clustr_area = np.array([50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300, 325, 350])
cluster_prob_raw = np.round(gct._transform_to_pvals(clustr_area, clthr._null_cluster_sizes.astype('float')),4)
cluster_prob_raw = np.round(gct._transform_to_pvals(clustr_area, clthr._null_cluster_sizes.astype('float')),4)

null_cluster_sizes = sp.dok_matrix.toarray(clthr._null_cluster_sizes)

#store the outputs...
thresmap_nifti = map2nifti(fds, data=res.fa.featurewise_thresh)
sig_nifti = map2nifti(fds, data=res.fa.clusters_featurewise_thresh)
fwesig_nifti = map2nifti(fds, data=res.fa.clusters_fwe_thresh)

thresmap_nifti.to_filename(slc_path2 + '/' + cond[xCond] + '_sl_thresmap.nii')
sig_nifti.to_filename(slc_path2 + '/' + cond[xCond] + '_sl_sigmap.nii')
fwesig_nifti.to_filename(slc_path2 + '/' + cond[xCond] + '_sl_fwesigmap.nii')


#draw histogram: # of voxels within a random cluster

import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
from scipy import stats


bin_num = 20
null_cluster_sizes = np.round(null_cluster_sizes, decimals=4)
null_cluster_sizes = np.array(null_cluster_sizes).reshape((1,-1))
null_cluster_sizes = null_cluster_sizes[0,0:bin_num]
bins = np.linspace(0, 20, bin_num)
xbar = np.arange(0,bin_num)
xbar = np.array(xbar).reshape((-1,)) +1
cluster_hist, cluster_bin_edges = np.histogram(null_cluster_sizes, bins=bin_num)
y = null_cluster_sizes.reshape((-1,))
plt.xticks(fontsize=13)
plt.yticks(fontsize=13)
plt.xlim(0,len(null_cluster_sizes))
plt.bar(xbar, y)

mu = np.round(stats.mode(null_cluster_sizes), 3) #M
sigma = np.round(np.std(null_cluster_sizes), 3)

n, bins, patches = plt.hist(null_cluster_sizes,
                            bins=bin_num,
                            density=True,
                            facecolor='mediumpurple',
                            edgecolor='lightgrey',
                            alpha=0.8)
#add a best fit line
y = mlab.normpdf(bins, mu, sigma)
l = plt.plot(bins, y, 'g--', linewidth=1)

plt.xlabel('# of voxels in a cluster', fontsize=13)
plt.ylabel('Frequency', fontsize=13)
plt.title(r'%s Histogram %s average cluster size.: M=%2.3f(%2.3f)'
          % (cond[xCond], 'searchlight', mu, sigma),
          fontsize=13)
plt.xticks(fontsize=13)
plt.yticks(fontsize=13)
plt.xlim(1,len(null_cluster_sizes))
plt.grid(axis='y', alpha=0.8)
graph_name = "%(path)s/fig/%(cond)s_%(roi)s_null_dist" % {"path": resultDir,
                                                          "cond": cond[xCond],
                                                          "roi": ROI[xROI]}
plt.savefig(graph_name + ".pdf", transparent=True)
plt.savefig(graph_name + ".png")
plt.show()







clusterstats.clusterstats.prob_corrected


clustr_sizes = clthr._null_cluster_sizes.astype('float')
clustr_sizes = np.asarray(clustr_sizes)

tmp_nifti = map2nifti(fds, data=tmp_perm)
tmp_nifti.to_filename(tmp_perm_subj_nii_file)
#look into res.a for all kinds of stats (# of clusters, their locations, significance etc)
res.fa.clusters.fdr_bh_thresh


cluster_probs_raw = gct._transform_to_pvals(np.array([40, 60, 80, 100, 120, 140]), clthr._null_clsuter_sizes.astype('float'))

cluster_probs_raw = gct._transform_to_pvals(np.array([40, 60, 80]),
                                            clthr._null_cluster_sizes.astype('float')
                                            )



