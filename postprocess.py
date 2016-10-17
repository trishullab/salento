import argparse
import numpy as np

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('kld_out', type=str, nargs=1,
                       help='kld.out file')
    argparser.add_argument('--topk', type=float, default=None,
                       help='sort top-k% of KLD values and print the top KLD from each package')
    argparser.add_argument('--plot', type=str, default=None,
           help='outfile for plotting all KLDs on a heat map, drawing a cutoff line if --topk is used')
    args = argparser.parse_args()
    if args.topk is None and args.plot is None:
        argparser.error('Provide at least one option')

    cutoff = 0
    klds = read_klds(args.kld_out[0])

    if args.topk is not None:
        cutoff = do_topk(klds, args.topk)
    if args.plot:
        do_plot(klds, args.plot, cutoff)

def do_plot(klds, plotfile, cutoff):
    import matplotlib.pyplot as plt
    x = np.array(range(len(klds)))
    y = np.array([kld for (_, _, kld) in klds])
    plt.hist2d(x, y, bins=[25,25])
    plt.colorbar()
    plt.xlabel('Program models', fontsize='large')
    plt.ylabel('Anomaly scores', fontsize='large')
    if cutoff > 0:
        plt.axhline(cutoff, color='w')
    plt.savefig(plotfile, bbox_inches='tight')

def do_topk(klds, topk):
    top_klds = sorted(klds, key=lambda x: -x[2])[:int(np.ceil(len(klds) * topk / 100))]
    packs, t = [], []
    for p, l, k in top_klds:
        if p not in packs:
            packs += [p]
            t += [(p,l, k)]
    top_klds = t
    print('\n'.join(['{} {} {}'.format(p, l, k) for p, l, k in top_klds]))
    return top_klds[-1][2]

def read_klds(outfile):
    klds = [] # list of triples (package, location, kld)
    with open(outfile) as f:
        for line in f:
            if line.startswith('###'):
                pack = line.split('### ')[1].rstrip('\n')
            elif line.startswith('  '):
                loc = line.split(':')[0].strip()
                kld = float(line.split(':')[1])
                klds.append((pack, loc, kld))
    return klds

if __name__ == '__main__':
    main()
