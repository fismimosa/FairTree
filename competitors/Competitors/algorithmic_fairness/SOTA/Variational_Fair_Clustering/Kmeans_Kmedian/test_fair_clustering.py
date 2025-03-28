import argparse
import os
import sys
import os.path as osp
import numpy as np
from sklearn.preprocessing import scale
from src.fair_clustering import fair_clustering, km_init
import src.utils as utils
from src.dataset_load import read_dataset,dataset_names
from src.utils  import get_fair_accuracy, get_fair_accuracy_proportional, normalizefea, Logger, str2bool
from data_visualization import plot_clusters_vs_lambda, plot_fairness_vs_clusterE, plot_convergence, plot_balance_vs_clusterE
import random
import warnings
import timeit
warnings.filterwarnings('ignore')

import random
#random.seed(0)
#np.random.seed(0)


def  main(args):

    if args.seed is not None:
        np.random.seed(args.seed)
        random.seed(args.seed)
        print("Seed set to "+str(args.seed))

    ## Options
    seedValue = args.seed
    dataset = args.dataset
    runNo = args.runNo
    kArg = args.K
    cluster_option = args.cluster_option
    data_dir = osp.join(args.data_dir, dataset)
    output_path = osp.join(data_dir,dataset+"_K_"+str(kArg))#+"_Run_"+str(runNo))
    
    #print('Output Path'+output_path)
    #print('Data dir'+data_dir)
    if not osp.exists(data_dir):
        os.makedirs(data_dir)
    if not osp.exists(output_path):
        os.makedirs(output_path)
   
    ## plotting options
    plot_option_clusters_vs_lambda = args.plot_option_clusters_vs_lambda
    plot_option_fairness_vs_clusterE = args.plot_option_fairness_vs_clusterE
    plot_option_balance_vs_clusterE = args.plot_option_balance_vs_clusterE
    plot_option_convergence = args.plot_option_convergence

    # ###  Data load
    savepath_compare =  osp.join(data_dir,dataset+'_'+str(kArg)+'_'+str(seedValue)+'.npz')
    if not os.path.exists(savepath_compare):
        X_org, demograph, K = read_dataset(dataset, data_dir,args)
        if X_org.shape[0]>200000:
            np.savez_compressed(savepath_compare, X_org = X_org, demograph = demograph, K = K)
        else:
            np.savez(savepath_compare, X_org=X_org, demograph=demograph, K=K)

    else:
        datas = np.load(savepath_compare)
        X_org = datas['X_org']
        demograph = datas['demograph']
        K = datas['K'].item()

    log_path = osp.join(output_path,cluster_option+'_'+str(K)+'_log.txt')
    sys.stdout = Logger(log_path)
    # Scale and Normalize Features
    #X_org = scale(X_org, axis = 0)
    X = X_org#normalizefea(X_org)
    #print(X)
    print('loaded dataset')
    N, D = X.shape
    print('****************** RUN '+str(args.runNo)+' ***********************')
    print('Cluster number for dataset {} is {}'.format(dataset,K))
    V_list =  [np.array(demograph == j) for j in np.unique(demograph)]
    V_sum =  [x.sum() for x in V_list]
    print('Balance of the dataset {}'.format(min(V_sum)/max(V_sum)))

    print('Number of points in the dataset {}'.format(N))
#    J = len(V_sum)


    # demographic probability for each V_j

    u_V = [x/N for x in V_sum]  #proportional
    print('Demographic-probabilites: {}'.format(u_V))
    print('Demographic-numbers per group: {}'.format(V_sum))

    #############################################################################

    ######################## Run Fair clustering #################################

    #############################################################################
    #
    fairness = True # Setting False only runs unfair clustering

    elapsetimes = []
    avg_balance_set = []
    min_balance_set = []
    fairness_error_set = []
    E_cluster_set = []
    E_cluster_discrete_set = []
    bestacc = 1e10
    best_avg_balance = -1
    best_min_balance = -1

    if args.lmbda_tune:
        print('Lambda tune is true')
        lmbdas = np.arange(0,10000,100).tolist()
    else:
        lmbdas = [args.lmbda]

    length_lmbdas = len(lmbdas)

    l = None


    if (not 'A' in locals()) and cluster_option == 'ncut':
        alg_option = 'flann' if N>50000 else 'None'
        affinity_path = osp.join(data_dir, dataset +'_affinity_ncut.npz')
        knn = 20
        if not osp.exists(affinity_path):
            A = utils.create_affinity(X, knn, savepath = affinity_path, alg=alg_option)
        else:
            A = utils.create_affinity(X, knn, W_path = affinity_path)

    init_C_path = osp.join(data_dir,'{}_init_{}_{}_{}.npz'.format(dataset,cluster_option,K,seedValue))
    if not osp.exists(init_C_path):
        print('Generating initial seeds')
        C_init,l_init = km_init(X,kArg,seedValue,cluster_option)#'kmeans_plus')
        np.savez(init_C_path, C_init = C_init, l_init = l_init)

    else:
        print("Loading earlier seeds")
        temp = np.load(init_C_path)
        C_init = temp ['C_init'] # Load initial seeds
        l_init = temp ['l_init']
    
    st_tune_time = timeit.default_timer()
    for count,lmbda in enumerate(lmbdas):

        print('Inside Lambda ',lmbda)
        print('For K ',K)

        if cluster_option == 'ncut':

            C,l,elapsed,S,E = fair_clustering(X, K, u_V, V_list, lmbda, fairness, cluster_option, C_init = C_init, l_init =l_init,  A = A)

        else:
            
            C,l,elapsed,S,E = fair_clustering(X, K, u_V, V_list, seedValue,lmbda, fairness, cluster_option, C_init=C_init, l_init=l_init)

        min_balance, avg_balance = get_fair_accuracy(u_V,V_list,l,N,K)
        fairness_error = get_fair_accuracy_proportional(u_V,V_list,l,N,K)

        print('lambda = {}, \n fairness_error {: .2f} and \n avg_balance = {: .2f} \n min_balance = {: .2f}'.format(lmbda, fairness_error, avg_balance, min_balance))


        # Plot the figure with clusters

        if dataset in ['Synthetic', 'Synthetic-unequal'] and plot_option_clusters_vs_lambda == True:
            cluster_plot_location = osp.join(output_path, 'cluster_output')
            if not osp.exists(cluster_plot_location):
                os.makedirs(cluster_plot_location)

            filename = osp.join(cluster_plot_location, 'cluster-plot_fair_{}-{}_lambda_{}_RunNO_{}.png'.format(cluster_option,dataset,lmbda,runNo))
            plot_clusters_vs_lambda(X_org, l, filename, dataset, lmbda, fairness_error)
    #
        if avg_balance>best_avg_balance:
           best_avg_balance = avg_balance
           best_lambda_avg_balance = lmbda

        if min_balance>best_min_balance:
           best_min_balance = min_balance
           best_lambda_min_balance = lmbda

        if fairness_error<bestacc:
            bestacc = fairness_error
            best_lambda_acc = lmbda


        if plot_option_convergence == True and count==0:

            filename = osp.join(output_path,'Fair_{}_convergence_{}_RunNo_{}.png'.format(cluster_option,dataset,runNo))
            E_fair = E['fair_cluster_E']
            plot_convergence(cluster_option, filename, E_fair)


        print('Best fairness_error %0.4f over lambdas' %bestacc,'|Error lambda = ', best_lambda_acc)
        print('Best  Avg balance %0.4f over lambdas' %best_avg_balance,'| Avg Balance lambda = ', best_lambda_avg_balance)
        print('Best  Min balance %0.4f over lambdas' %best_min_balance,'| Min Balance lambda = ', best_lambda_min_balance)
        elapsetimes.append(elapsed)
        avg_balance_set.append(avg_balance)
        min_balance_set.append(min_balance)
        fairness_error_set.append(fairness_error)
        E_cluster_set.append(E['cluster_E'][-1])
        E_cluster_discrete_set.append(E['cluster_E_discrete'][-1])
    ft_tune_time = timeit.default_timer()
    print ('total time in tuning is  ',str(ft_tune_time-st_tune_time))
    avgelapsed = sum(elapsetimes)/len(elapsetimes)
    print ('avg elapsed ',avgelapsed)

    if plot_option_fairness_vs_clusterE == True and length_lmbdas > 1:


        savefile = osp.join(data_dir,'Fair_{}_fairness_vs_clusterEdiscrete_{}.npz'.format(cluster_option,dataset))
        filename = osp.join(output_path,'Fair_{}_fairness_vs_clusterEdiscrete_{}_Run_{}.png'.format(cluster_option,dataset,runNo))
        plot_fairness_vs_clusterE(cluster_option, savefile, filename, lmbdas, fairness_error_set, min_balance_set, avg_balance_set, E_cluster_discrete_set)

    if plot_option_balance_vs_clusterE == True and length_lmbdas > 1:

        savefile = osp.join(data_dir,'Fair_{}_balance_vs_clusterEdiscrete_{}.npz'.format(cluster_option,dataset))
        filename = osp.join(output_path,'Fair_{}_balance_vs_clusterEdiscrete_{}_Run_{}.png'.format(cluster_option,dataset,runNo))

        plot_balance_vs_clusterE(cluster_option, savefile, filename, lmbdas, fairness_error_set, min_balance_set, avg_balance_set, E_cluster_discrete_set)
        
    return E_cluster_discrete_set,fairness_error_set,avg_balance_set,min_balance_set