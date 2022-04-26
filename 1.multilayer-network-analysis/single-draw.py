#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2022/3/23 上午10:40
# @Author  : liu yuhan
# @FileName: multilayer-draw.py
# @Software: PyCharm

import json
import networkx as nx
from collections import defaultdict, Counter
import plotly.graph_objs as go


def dict_reverse(key_value_list):
    value_key_list = defaultdict(list)
    for key, value_list in key_value_list.items():
        for value in value_list:
            value_key_list[value].append(int(key))
    return value_key_list


def get_node_degree(node_list, link_list):
    """
    获取节点的度，并对节点的度进行排序，返回一个元祖list
    :param node_list:
    :param link_list:
    :return:
    """
    g_doc = nx.Graph()
    g_doc.add_nodes_from(node_list)
    g_doc.add_edges_from(link_list)
    return sorted(nx.degree(g_doc), key=lambda x: x[1], reverse=True)


class MultilayerAnalysis:
    def __init__(self, tech_point, output_path, node_size, line_width, related=False, rank=False):
        """
        :param tech_point: 需要进行分析的技术点
        :param related: 是否分析相关技术的选项，
            是：分析当前技术的所有相关子技术
            否：仅分析当前技术
        """
        self.rank = rank
        self.tech_point = [tech_point]
        # 转换为label
        self.trans2index()
        self.tech_point_list = []
        self.tech_link = []
        self.tech_net()
        # 是否处理相关节点
        if related:
            self.tech_point = self.tech_point_list
        # 输出
        self.output_path = output_path
        # 各类节点
        self.doc_l_list = []
        self.doc_p_list = []
        self.author_list = []
        self.inst_list = []
        # 内部连接
        self.doc_l_link = []
        self.doc_p_link = []
        self.author_link = []
        self.inst_link_co = []
        # 层间连接
        self.tech_doc_l = []
        self.tech_doc_p = []
        self.doc_l_author = []
        self.doc_p_author = []
        self.author_inst = []
        # 总的连接
        self.node_list = []
        self.tech_node = dict()
        self.doc_l_node = dict()
        self.doc_p_node = dict()
        self.author_node = dict()
        self.inst_node = dict()
        # 画图
        self.node_layout = dict()
        self.x_span = []
        self.y_span = []
        self.xn, self.yn, self.zn = [], [], []
        self.xe, self.ye, self.ze = [], [], []
        self.node_size = node_size
        self.line_width = line_width

    def trans2index(self):
        with open('../data/node/keyword2index.json', 'r', encoding='UTF-8') as file:
            keyword2index = json.load(file)
        tech_point_trans = []
        for node in self.tech_point:
            try:
                tech_point_trans.append(keyword2index[node.lower()])
            except KeyError:
                continue
        if not tech_point_trans:
            raise ValueError('tech_point is not exist.')
        self.tech_point = tech_point_trans

    def tech_net(self):
        """
        科技网络
        :return:
        """
        with open('../data/link/tech_tree.json', 'r', encoding='UTF-8') as file:
            tech_tree = json.load(file)
        tech_tree_reverse = dict_reverse(tech_tree)

        for tech in self.tech_point:
            farther_tech_point = tech_tree_reverse[tech][0]
            tech_related_list = tech_tree[str(farther_tech_point)]
            self.tech_point_list += tech_related_list
            for tech_related in tech_related_list:
                if tech == tech_related:
                    continue
                self.tech_link.append([tech, tech_related])

    def network_get(self):
        """
        这里需要获取四个网络
            技术网络：
                节点：技术
                连接：兄弟技术（同一父亲技术）
            科技文献网络：
                节点：专利、论文
                连接：专利引用、论文引用
            研究人员网络：
                节点：研究人员
                连接：研究人员合作
            机构网络：
                节点：机构
                连接：机构合作、机构供应链
        :return:
        """
        print('data getting---')
        print('    processing--- doc---')
        self.doc_net()
        print('    processing--- author---')
        self.author_net()
        print('    processing--- inst---')
        self.inst_net()
        print('trans---')
        print('    processing--- node---')
        self.node_trans()
        print('    processing--- link_intra---')
        self.link_trans_intra()
        print('    processing--- link_inter---')
        self.link_trans_inter()

    def node_trans(self):
        """
        节点的index进行修改
        :return:
        """
        index = 0
        for node_list_temper, to_node_temper in \
                zip([self.tech_point_list, self.doc_l_list, self.doc_p_list, self.author_list, self.inst_list],
                    [self.tech_node, self.doc_l_node, self.doc_p_node, self.author_node, self.inst_node]):
            for node in node_list_temper:
                self.node_list.append(index)
                to_node_temper[node] = index
                index += 1
        print('      node num %d' % len(self.node_list))

    def link_trans_intra(self):
        """
        层内连接的index进行修改
        目前无法考虑weight
        :return:
        """
        count = 0
        for link_list_temper, to_node_temper in \
                zip([self.tech_link, self.doc_l_link, self.doc_p_link, self.author_link, self.inst_link_co],
                    [self.tech_node, self.doc_l_node, self.doc_p_node, self.author_node, self.inst_node]):
            for i, link in enumerate(link_list_temper):
                link_list_temper[i] = [to_node_temper[link[0]], to_node_temper[link[1]]]
                count += 1
        print('      link-intra num %d' % count)

    def link_trans_inter(self):
        """
        层间连接的index进行修改
        目前无法考虑weight
        :return:
        """
        count = 0
        for link_list_temper, to_source_temper, to_target_temper in \
                zip([self.tech_doc_l, self.tech_doc_p, self.doc_l_author, self.doc_p_author, self.author_inst],
                    [self.tech_node, self.tech_node, self.doc_l_node, self.doc_p_node, self.author_node],
                    [self.doc_l_node, self.doc_p_node, self.author_node, self.author_node, self.inst_node]):
            for i, link in enumerate(link_list_temper):
                link_list_temper[i] = [to_source_temper[link[0]], to_target_temper[link[1]]]
                count += 1
        print('      link-inter num %d' % count)

    def doc_net_single(self, label):
        """
        这里网络构建的原则是，头和尾都在已有的list中，不进行扩展
        :param label:
        :return:
        """
        with open('../data/link/doc_' + label + '_keyword_dict.json') as file:
            doc_tech = json.load(file)
        with open('../data/link/doc_citing_' + label + '.json') as file:
            doc_citing = json.load(file)
        tech_doc = dict_reverse(doc_tech)
        # 收集节点
        doc_list = []
        tech_doc_link = []
        for tech in self.tech_point:
            doc_list_temper = tech_doc[tech]
            for doc in doc_list_temper:
                tech_doc_link.append([tech, doc])
            doc_list += doc_list_temper
        # 收集连接
        doc_link_list = []
        for source in doc_list:
            if str(source) not in doc_citing:
                continue
            target_list = doc_citing[str(source)]
            for target in target_list:
                if target in doc_list:
                    doc_link_list.append([source, target])

        if self.rank:
            doc_degree = get_node_degree(doc_list, doc_link_list)
            doc_list = [_[0] for _ in doc_degree[:50]]
            # 进行一轮清理
            doc_link_list_ = doc_link_list.copy()
            doc_link_list = []
            for doc_link in doc_link_list_:
                if doc_link[0] in doc_list and doc_link[1] in doc_list:
                    doc_link_list.append(doc_link)
            tech_doc_link_ = tech_doc_link.copy()
            tech_doc_link = []
            for tech_doc in tech_doc_link_:
                if tech_doc[1] in doc_list:
                    tech_doc_link.append(tech_doc)

        return doc_list, doc_link_list, tech_doc_link

    def author_net_single(self, label):
        """
        服务于作者的合作网络，机构的合作网络
        :param label:
        :return:
        """
        with open('../data/link/doc_' + label + '_author_dict.json') as file:
            doc_author = json.load(file)
        if label == 'literature':
            doc_list = self.doc_l_list
        else:
            doc_list = self.doc_p_list
        # 收集节点，收集连接
        author_list = []
        doc_author_list = []
        author_link_dict_weighted = Counter()
        for doc in doc_list:
            try:
                author_list_temper = sorted(doc_author[str(doc)])
            except KeyError:
                continue
            for author in author_list_temper:
                doc_author_list.append([doc, author])

            author_list += author_list_temper
            temper_length = len(author_list_temper)
            if temper_length < 2:
                continue
            for i in range(0, temper_length - 1):
                for j in range(i + 1, temper_length):
                    author_link_dict_weighted[str(author_list_temper[i]) + ' ' + str(author_list_temper[j])] += 1
        # 权重改写
        author_link_list = [[int(author) for author in author_list.split()] + [weight]
                            for author_list, weight in author_link_dict_weighted.items()]
        author_list = sorted(list(set(author_list)))
        return author_list, author_link_list, doc_author_list

    def inst_co_net_single(self, label):
        """
        服务于作者的合作网络，机构的合作网络
        :param label:
        :return:
        """
        with open('../data/link/doc_' + label + '_inst_dict.json') as file:
            doc_inst = json.load(file)
        if label == 'literature':
            doc_list = self.doc_l_list
        else:
            doc_list = self.doc_p_list
        # 收集节点，收集连接
        inst_list = []
        inst_link_dict_weighted = Counter()
        for doc in doc_list:
            try:
                inst_list_temper = sorted(doc_inst[str(doc)])
            except KeyError:
                continue
            inst_list += inst_list_temper
            temper_length = len(inst_list_temper)
            if temper_length < 2:
                continue
            # 合作网络写入
            for i in range(0, temper_length - 1):
                for j in range(i + 1, temper_length):
                    inst_link_dict_weighted[str(inst_list_temper[i]) + ' ' + str(inst_list_temper[j])] += 1
        # 去重
        inst_list = sorted(list(set(inst_list)))
        # 权重改写
        inst_link_list = [[int(inst) for inst in inst_couple.split()] + [weight]
                          for inst_couple, weight in inst_link_dict_weighted.items()]

        return inst_list, inst_link_list

    def author_inst_get(self):
        """
        :return:
        真的是很奇怪的部分。
        """
        with open('../data/link/inst_author_dict.json') as file:
            inst_author = json.load(file)
        inst_author_link = []
        for source in self.inst_list:
            try:
                target_list = inst_author[str(source)]
            except KeyError:
                continue
            for target in target_list:
                if target in self.author_list:
                    inst_author_link.append([target, source])
        return inst_author_link

    def doc_net(self):
        """
        科技文献，专利+论文
        :return:
        """
        self.doc_l_list, self.doc_l_link, self.tech_doc_l = self.doc_net_single('literature')
        self.doc_p_list, self.doc_p_link, self.tech_doc_p = self.doc_net_single('patent')
        print('      node num %d' % (len(self.doc_p_list) + len(self.doc_l_list)))
        # 这里需要对两个科技网络进行融合

    def author_net(self):
        """
        研究人员网络
        :return:
        """
        # 很遗憾现在只有论文的作者
        author_l_list, author_l_link_list, self.doc_l_author = self.author_net_single('literature')
        author_p_list, author_p_link_list, self.doc_p_author = [], [], []
        self.author_list = sorted(list(set(author_l_list + author_p_list)))
        print('      node num %d' % len(self.author_list))
        self.author_link = author_l_link_list + author_p_link_list

    def inst_net(self):
        """
        机构网络
        :return:
        """
        inst_l_list, inst_l_link_list = self.inst_co_net_single('literature')
        inst_p_list, inst_p_link_list = self.inst_co_net_single('patent')
        self.inst_list = sorted(list(set(inst_l_list + inst_p_list)))
        print('      node num %d' % len(self.inst_list))
        self.inst_link_co = inst_l_link_list + inst_p_link_list
        self.author_inst = self.author_inst_get()

    def network_draw(self, layer):
        """
        最后一步画图，
        :return:
        """
        print('draw---')
        print('    processing--- layout---')
        self.get_layout()
        print('    processing--- get_draw_data---')
        self.get_draw_data(layer)
        print('    processing--- draw---')
        self.draw(layer)

    def get_span(self):
        """
        坐标跨度计算，计算节点坐标在 x,y 两个维度上的跨度
        :return:
        """
        x_max = max([self.node_layout[i]['pos'][0] for i in self.node_layout])
        y_max = max([self.node_layout[i]['pos'][1] for i in self.node_layout])
        x_min = min([self.node_layout[i]['pos'][0] for i in self.node_layout])
        y_min = min([self.node_layout[i]['pos'][1] for i in self.node_layout])
        self.x_span = [x_max, x_min]
        self.y_span = [y_max, y_min]

    def get_h(self):
        x_span = self.x_span[0] - self.x_span[1]
        y_span = self.y_span[0] - self.y_span[1]
        return (x_span * y_span) ** 0.5

    def get_center(self):
        """
        对layout进行调整
        :return:
        """
        return (self.x_span[0] - self.x_span[1]) / 2, (self.y_span[0] - self.y_span[1]) / 2

    def get_layout(self):
        """
        这个地方有两种方案
            1.四层网络合起来做一个layout 这个方案
            2.每层单独做layout
            目前采用方案1
        :return:
        """
        g_layout = nx.Graph()
        g_layout.add_nodes_from(self.node_list)
        g_layout.add_edges_from(
            self.tech_link + self.doc_l_link + self.doc_p_link + self.author_link + self.inst_link_co +
            self.tech_doc_l + self.tech_doc_p + self.doc_l_author + self.doc_p_author + self.author_inst)
        pos = nx.spring_layout(g_layout, iterations=15)

        for node in list(g_layout.nodes):
            self.node_layout[node] = {'pos': list(pos[node])}
        self.get_span()

    def get_draw_data(self, layer):
        """
        节点连接转换成三维
        :return:
        """

        # 二维变三维
        def get_xyz_3d(node_list, h):
            node_xyz_dict = dict()
            for node in node_list:
                xyz = self.node_layout[node]['pos'] + [h]
                node_xyz_dict[node] = xyz
            return node_xyz_dict

        # 节点
        def get_node_xyz(nodes_xyz):
            xn_, yn_, zn_ = [], [], []
            for node in nodes_xyz:
                xn_.append(nodes_xyz[node][0])
                yn_.append(nodes_xyz[node][1])
                zn_.append(nodes_xyz[node][2])
            return xn_, yn_, zn_

        # 连接
        # 层内连接
        def get_link_xyz_intra(link_list, nodes_xyz):
            xe_, ye_, ze_ = [], [], []
            for link in link_list:
                xe_ += [nodes_xyz[link[0]][0], nodes_xyz[link[1]][0], None]
                ye_ += [nodes_xyz[link[0]][1], nodes_xyz[link[1]][1], None]
                ze_ += [nodes_xyz[link[0]][2], nodes_xyz[link[1]][2], None]
            return xe_, ye_, ze_

        if layer == 'inst':
            node_inst_xyz = get_xyz_3d(list(self.inst_node.values()), h=0)
            node_xyz_list = [node_inst_xyz]
            link_inf_list = [[self.inst_link_co, node_inst_xyz]]
        elif layer == 'author':
            node_author_xyz = get_xyz_3d(list(self.author_node.values()), h=0)
            node_xyz_list = [node_author_xyz]
            link_inf_list = [[self.author_link, node_author_xyz]]
        elif layer == 'doc':
            node_doc_l_xyz = get_xyz_3d(list(self.doc_l_node.values()), h=0)
            node_doc_p_xyz = get_xyz_3d(list(self.doc_p_node.values()), h=0)
            node_xyz_list = [node_doc_l_xyz, node_doc_p_xyz]
            link_inf_list = [[self.doc_l_link, node_doc_l_xyz], [self.doc_p_link, node_doc_p_xyz]]
        else:
            raise KeyError('layer not exist')

        for node_xyz in node_xyz_list:
            xn_temper, yn_temper, zn_temper = get_node_xyz(node_xyz)
            self.xn += xn_temper
            self.yn += yn_temper
            self.zn += zn_temper

        for link, node_xyz in link_inf_list:
            xe_temper, ye_temper, ze_temper = get_link_xyz_intra(link, node_xyz)
            self.xe += xe_temper
            self.ye += ye_temper
            self.ze += ze_temper

    def draw(self, layer):
        """
        画图
        :return:
        """
        alpha = 0.75
        if layer == 'inst':
            color = 'rgba(0,197,205,1)'
        elif layer == 'author':
            color = 'rgba(238,221,130,1)'
        elif layer == 'doc':
            color = 'rgba(132,112,255,1)'
        else:
            raise KeyError('layer not exist')
        trace_node = go.Scatter3d(x=self.xn, y=self.yn, z=self.zn,
                                  mode='markers',
                                  name='actors',
                                  marker=dict(symbol='circle',
                                              size=node_size,  # size of nodes
                                              color=color,
                                              colorscale='Viridis'
                                              ),
                                  # text=labels,
                                  hoverinfo='text'
                                  )

        trace_line = go.Scatter3d(x=self.xe, y=self.ye, z=self.ze,
                                  mode='lines',
                                  line=dict(width=line_width,
                                            color=color
                                            ),  # 线的颜色与尺寸
                                  hoverinfo='none'
                                  )
        axis = dict(showbackground=False,
                    showline=False,
                    zeroline=False,
                    showgrid=False,
                    showticklabels=False,
                    title=''
                    )

        layout = go.Layout(title="multilayer_analysis",
                           width=1500,
                           height=1500,
                           showlegend=True,
                           scene=dict(xaxis=dict(axis),
                                      yaxis=dict(axis),
                                      zaxis=dict(axis),
                                      ),
                           margin=dict(t=100),
                           hovermode='closest',
                           annotations=[dict(showarrow=False,
                                             xref='paper',
                                             yref='paper',
                                             x=0,
                                             y=0.1,
                                             xanchor='left',
                                             yanchor='bottom',
                                             font=dict(size=14)
                                             )
                                        ]
                           )

        data_plot = [trace_line, trace_node]
        fig = go.Figure(data=data_plot, layout=layout)
        # 生成 html 格式文件
        fig.write_html(self.output_path)


if __name__ == '__main__':
    tech_point = 'health care'
    # tech_point = 'acceleration deceleration'
    output_path = '../data/output/single_analysis.html'
    node_size, line_width = 3, 1
    multi_analysis = MultilayerAnalysis(tech_point, output_path, node_size, line_width,
                                        related=False, rank=True)
    multi_analysis.network_get()
    multi_analysis.network_draw('author')
