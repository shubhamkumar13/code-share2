import multiprocessing
import json
import os, glob
import pandas as pd
import pandas.io.json as pdjson
import seaborn as sns

sns.set(style="whitegrid")


def run(sz):
    data_frames = []

    for file in glob.glob("benchfiles/*.orunchrt_{}_*.summary.bench".format(sz)):
        print(file)
        with open(file) as f:
            data = []
            for l in f:
                j = json.loads(l)
                j['name'] = j['name'].split('.orunchrt')[0]
                data.append(j)
            df = pd.json_normalize(data)
            df['variant'] = file.replace(".summary.bench","").replace("benchfiles/", "")
            data_frames.append(df)

    # print(data_frames)
    df = pd.concat (data_frames, sort=False)
    df = df.sort_values(['name'])
    # Uncomment the following to display all the lines in pandas output
    pd.set_option('display.max_rows', df.shape[0]+1)

    df.filter(['name','variant','time_secs'])

    g = sns.catplot (x='name', y='time_secs', hue='variant', data = df, kind ='bar', aspect=16)
    g.set_xticklabels(rotation=90)
    g.savefig("./graphs/time_{}.jpg".format(sz))

    # returns a dictionary with {key = name : value : metric}
    # the metric corresponds to the variant
    def create_column(df, variant, metric):
        df = pd.DataFrame.copy(df)
        variant_metric_name = list([ zip(df[metric], df[x], df['name'])
                for x in df.columns.array if x == "variant" ][0])
        name_metric = {n:t for (t, v, n) in variant_metric_name if v == variant}
        return name_metric

    def add_display_name(df, variant, metric):
        name_metric = create_column(pd.DataFrame.copy(df), variant, metric)
        disp_name = [name+" ("+str(round(name_metric[name], 2))+")" for name in df["name"]]
        df["display_name"] = pd.Series(disp_name, index=df.index)
        return df

    def normalise(df, variant, topic, additionalTopics=[]):
        df = add_display_name(df, variant, topic)
        df = df.sort_values(["name","variant"])
        grouped = df.filter(items=['name',topic,'variant','display_name']+additionalTopics).groupby('variant')
        ndata_frames = []
        for group in grouped:
            (v,data) = group
            if(v != variant):
                data['b'+topic] = grouped.get_group(variant)[topic].values
                data[['n'+topic]] = data[[topic]].div(grouped.get_group(variant)[topic].values, axis=0)
                for t in additionalTopics:
    #                 print(variant, t)
                    data[[t]] = grouped.get_group(variant)[t].values
                ndata_frames.append(data)
        df = pd.concat (ndata_frames)
        return df

    def plot_normalised(df, variant, topic):
        df = pd.DataFrame.copy(df)
        df.sort_values(by=[topic],inplace=True)
        df[topic] = df[topic] - 1
        g = sns.catplot (x="display_name", y=topic, hue='variant', data = df, kind ='bar', aspect=16, bottom=1)
        g.set_xticklabels(rotation=90)
        g.ax.legend(loc=8)
        g._legend.remove()
        g.ax.set_xlabel("Benchmarks")
        return g
        # g.ax.set_yscale('log')

    ndf = normalise(df, '4.12.0+domains+effects_1.orunchrt_{}_8'.format(sz), 'time_secs')
    g = plot_normalised(ndf, '4.12.0+domains+effects_1.orunchrt_{}_8'.format(sz), 'ntime_secs')
    g.savefig("./graphs/time_normalised_{}.jpg".format(sz))

    g = sns.catplot (x='name', y='gc.major_collections', hue='variant', data = df, kind ='bar', aspect=4)
    g.set_xticklabels(rotation=90)
    g.savefig("./graphs/major_collections_{}.jpg".format(sz))

    ndf = normalise(df, '4.12.0+domains+effects_1.orunchrt_{}_8'.format(sz), 'gc.major_collections')
    g = plot_normalised(ndf, '4.12.0+domains+effects_1.orunchrt_{}_8'.format(sz), 'ngc.major_collections')
    g.savefig("./graphs/major_collections_normalised_{}.jpg".format(sz))

    g = sns.catplot (x='name', y='gc.minor_collections', hue='variant', data = df, kind ='bar', aspect=4)
    g.set_xticklabels(rotation=90)
    g.savefig("./graphs/minor_collections_{}.jpg".format(sz))

    ndf = normalise(df, '4.12.0+domains+effects_1.orunchrt_{}_8'.format(sz), 'gc.minor_collections')
    g = plot_normalised(ndf, '4.12.0+domains+effects_1.orunchrt_{}_8'.format(sz), 'ngc.minor_collections')
    g.savefig("./graphs/minor_collections_normalised_{}.jpg".format(sz))

pool = multiprocessing.Pool(4)
pool.map(run, ["256k", "512k", "1M", "2M", "4M"])