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


class MultilayerAnalysis:
    def __init__(self, tech_point, output_path, node_size, line_width, related=False):
        """
        :param tech_point: 需要进行分析的技术点
        :param related: 是否分析相关技术的选项，
            是：分析当前技术的所有子技术
            否：仅分析当前技术
        """
        if not related:
            self.tech_point = [tech_point]
        else:
            # 技术点之前目前没有连接
            self.tech_point = [tech_point]
        self.output_path = output_path
        # 转换为label
        self.trans2index()
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
        self.inst_link_supply = []
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
        self.tech_point = tech_point_trans

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
                zip([self.tech_point, self.doc_l_list, self.doc_p_list, self.author_list, self.inst_list],
                    [self.tech_node, self.doc_l_node, self.doc_p_node, self.author_node, self.inst_node]):
            for node in node_list_temper:
                self.node_list.append(index)
                to_node_temper[node] = index
                index += 1

    def link_trans_intra(self):
        """
        层内连接的index进行修改
        目前无法考虑weight
        :return:
        """
        for link_list_temper, to_node_temper in \
                zip([self.doc_l_link, self.doc_p_link, self.author_link, self.inst_link_co, self.inst_link_supply],
                    [self.doc_l_node, self.doc_p_node, self.author_node, self.inst_node, self.inst_node]):
            for i, link in enumerate(link_list_temper):
                link_list_temper[i] = [to_node_temper[link[0]], to_node_temper[link[1]]]

    def link_trans_inter(self):
        """
        层间连接的index进行修改
        目前无法考虑weight
        :return:
        """
        for link_list_temper, to_source_temper, to_target_temper in \
                zip([self.tech_doc_l, self.tech_doc_p, self.doc_l_author, self.doc_p_author, self.author_inst],
                    [self.tech_node, self.tech_node, self.doc_l_node, self.doc_p_node, self.author_node],
                    [self.doc_l_node, self.doc_p_node, self.author_node, self.author_node, self.inst_node]):
            for i, link in enumerate(link_list_temper):
                link_list_temper[i] = [to_source_temper[link[0]], to_target_temper[link[1]]]

    # def tech_net(self):
    #     """
    #     科技网络
    #     :return:
    #     """
    #     pass

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

    def inst_supply_get(self):
        """
        :return:
        """
        with open('../data/link/inst_supply_dict.json') as file:
            inst_supply = json.load(file)
        inst_link = []
        for source in self.inst_list:
            try:
                target_list = inst_supply[str(source)]
            except KeyError:
                continue
            for target in target_list:
                if target in self.inst_list:
                    inst_link.append([source, target])
        return inst_link

    def author_inst_get(self):
        """
        :return:
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
        self.author_link = author_l_link_list + author_p_link_list

    def inst_net(self):
        """
        机构网络
        :return:
        """
        inst_l_list, inst_l_link_list = self.inst_co_net_single('literature')
        inst_p_list, inst_p_link_list = self.inst_co_net_single('patent')
        self.inst_list = sorted(list(set(inst_l_list + inst_p_list)))
        self.inst_link_co = inst_l_link_list + inst_p_link_list
        self.inst_link_supply = self.inst_supply_get()
        self.author_inst = self.author_inst_get()

    def network_draw(self):
        """
        最后一步画图，
        :return:
        """
        print('draw---')
        print('    processing--- layout---')
        self.get_layout()
        print('    processing--- get_draw_data---')
        self.get_draw_data()
        print('    processing--- draw---')
        self.draw()

    def get_layout(self):
        """
        这个地方有两种方案
            1.四层网络合起来做一个layout
            2.每层单独做layout
            目前采用方案1
        :return:
        """
        g_layout = nx.Graph()
        g_layout.add_nodes_from(self.node_list)
        g_layout.add_edges_from(
            self.doc_l_link + self.doc_p_link + self.author_link + self.inst_link_co + self.inst_link_supply +
            self.tech_doc_l + self.tech_doc_p + self.doc_l_author + self.doc_p_author + self.author_inst)
        pos = nx.spectral_layout(g_layout)

        for node in list(g_layout.nodes):
            self.node_layout[node] = {'pos': list(pos[node])}

    def get_draw_data(self):
        """
        节点连接转换成三维
        :return:
        """

        # 坐标跨度计算，计算节点坐标在 x,y 两个维度上的跨度
        def get_h(xyz_dict):
            x_max = max([xyz_dict[i]['pos'][0] for i in xyz_dict])
            y_max = max([xyz_dict[i]['pos'][1] for i in xyz_dict])
            x_min = min([xyz_dict[i]['pos'][0] for i in xyz_dict])
            y_min = min([xyz_dict[i]['pos'][1] for i in xyz_dict])
            x_span = x_max - x_min
            y_span = y_max - y_min
            return (x_span * y_span) ** 0.5

        # 二维变三维
        def get_xyz_3d(node_list, h):
            node_xyz_dict = dict()
            for node in node_list:
                xyz = self.node_layout[node]['pos'] + [h]
                node_xyz_dict[node] = xyz
            return node_xyz_dict

        high = get_h(self.node_layout)
        node_tech_xyz = get_xyz_3d(list(self.tech_node.values()), h=0)
        node_doc_l_xyz = get_xyz_3d(list(self.doc_l_node.values()), h=high)
        node_doc_p_xyz = get_xyz_3d(list(self.doc_p_node.values()), h=high)
        node_author_xyz = get_xyz_3d(list(self.author_node.values()), h=high * 2)
        node_inst_xyz = get_xyz_3d(list(self.inst_node.values()), h=high * 3)

        # 节点
        def get_node_xyz(nodes_xyz):
            xn_, yn_, zn_ = [], [], []
            for node in nodes_xyz:
                xn_.append(nodes_xyz[node][0])
                yn_.append(nodes_xyz[node][1])
                zn_.append(nodes_xyz[node][2])
            return xn_, yn_, zn_

        for node_xyz in [node_tech_xyz, node_doc_l_xyz, node_doc_p_xyz, node_author_xyz, node_inst_xyz]:
            xn_temper, yn_temper, zn_temper = get_node_xyz(node_xyz)
            self.xn += xn_temper
            self.yn += yn_temper
            self.zn += zn_temper

        # 连接
        # 层内连接
        def get_link_xyz_intra(link_list, nodes_xyz):
            xe_, ye_, ze_ = [], [], []
            for link in link_list:
                xe_ += [nodes_xyz[link[0]][0], nodes_xyz[link[1]][0], None]
                ye_ += [nodes_xyz[link[0]][1], nodes_xyz[link[1]][1], None]
                ze_ += [nodes_xyz[link[0]][2], nodes_xyz[link[1]][2], None]
            return xe_, ye_, ze_

        for link, node_xyz in \
                zip([self.doc_l_link, self.doc_p_link, self.author_link, self.inst_link_co, self.inst_link_supply],
                    [node_doc_l_xyz, node_doc_p_xyz, node_author_xyz, node_inst_xyz, node_inst_xyz]):
            xe_temper, ye_temper, ze_temper = get_link_xyz_intra(link, node_xyz)
            self.xe += xe_temper
            self.ye += ye_temper
            self.ze += ze_temper

        # 层间连接
        def get_link_xyz_inter(link_list, nodes_xyz_source, nodes_xyz_target):
            xe_, ye_, ze_ = [], [], []
            for link in link_list:
                xe_ += [nodes_xyz_source[link[0]][0], nodes_xyz_target[link[1]][0], None]
                ye_ += [nodes_xyz_source[link[0]][1], nodes_xyz_target[link[1]][1], None]
                ze_ += [nodes_xyz_source[link[0]][2], nodes_xyz_target[link[1]][2], None]
            return xe_, ye_, ze_

        for link, node_xyz_source, node_xyz_target in \
                zip([self.tech_doc_l, self.tech_doc_p, self.doc_l_author, self.doc_p_author, self.author_inst],
                    [node_tech_xyz, node_tech_xyz, node_doc_l_xyz, node_doc_p_xyz, node_author_xyz],
                    [node_doc_l_xyz, node_doc_p_xyz, node_author_xyz, node_author_xyz, node_inst_xyz]):
            xe_temper, ye_temper, ze_temper = get_link_xyz_inter(link, node_xyz_source, node_xyz_target)
            self.xe += xe_temper
            self.ye += ye_temper
            self.ze += ze_temper

    def draw(self):
        """
        画图
        :return:
        """
        trace_node = go.Scatter3d(x=self.xn, y=self.yn, z=self.zn,
                                  mode='markers',
                                  name='actors',
                                  marker=dict(symbol='circle',
                                              size=node_size,  # size of nodes
                                              # color=color_list_1 + color_list_2 + color_list_3,  # color of nodes
                                              colorscale='Viridis'
                                              ),
                                  # text=labels,
                                  hoverinfo='text'
                                  )

        trace_line = go.Scatter3d(x=self.xe, y=self.ye, z=self.ze,
                                  mode='lines',
                                  line=dict(width=line_width,
                                            # color=['rgba(202,255,135,0.8)', 'rgba(202,255,135,0.8)', 0] *
                                            #       int(len(Xe_1) / 3) +
                                            #       ['rgba(25,206,250,0.8)', 'rgba(25,206,250,0.8)', 0] *
                                            #       int(len(Xe_2) / 3) +
                                            #       ['rgba(245,133,15,0.8)', 'rgba(245,133,15,0.8)', 0] *
                                            #       int(len(Xe_3) / 3) +
                                            #       ['rgba(100,100,100,0.7)', 'rgba(100,100,100,0.7)', 0] *
                                            #       int(len(Xe_12 + Xe_23) / 3)
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
    tech_point = 'numerical control system'
    output_path = '../data/output/multilayer_analysis.html'
    node_size, line_width = 1, 0.5
    multi_analysis = MultilayerAnalysis(tech_point, output_path, node_size, line_width, related=False)
    multi_analysis.network_get()
    multi_analysis.network_draw()
