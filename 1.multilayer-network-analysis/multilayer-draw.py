#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2022/3/23 上午10:40
# @Author  : liu yuhan
# @FileName: multilayer-draw.py
# @Software: PyCharm
import json
import pandas as pd
from collections import defaultdict, Counter
from tqdm import tqdm


def dict_reverse(key_value_list):
    value_key_list = defaultdict(list)
    for key, value_list in key_value_list.items():
        for value in value_list:
            value_key_list[value].append(int(key))
    return value_key_list


class MultilayerAnalysis:
    def __init__(self, tech_point, related=False):
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

    def network_draw(self):
        """
        最后一步画图，
        :return:
        """

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
        :param role:
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
        :param role:
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


if __name__ == '__main__':
    tech_point = 'high speed'
    multi_analysis = MultilayerAnalysis(tech_point)
    multi_analysis.network_get()
