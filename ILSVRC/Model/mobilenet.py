import torch
import torch.nn as nn 
from torch.autograd import Variable
import torch.nn.functional as F
import numpy as np 
import cv2
from skimage import measure
from utils.func import *
import torchvision.models as models



class Model(nn.Module):
    def __init__(self,args):
        super(Model, self).__init__()
        def conv_bn(inp, oup, stride):
            return nn.Sequential(
                nn.Conv2d(inp, oup, 3, stride, 1, bias=False),
                nn.BatchNorm2d(oup),
                nn.ReLU(inplace=True)
            )
        def conv_dw(inp, oup, stride):
            return nn.Sequential(
                nn.Conv2d(inp, inp, 3, stride, 1, groups=inp, bias=False),
                nn.BatchNorm2d(inp),
                nn.ReLU(inplace=True),
    
                nn.Conv2d(inp, oup, 1, 1, 0, bias=False),
                nn.BatchNorm2d(oup),
                nn.ReLU(inplace=True),
            )
        self.model = nn.Sequential(
            conv_bn(  3,  32, 2),  ## ->112
            conv_dw( 32,  64, 1),
            conv_dw( 64, 128, 2),  ## ->56
            conv_dw(128, 128, 1),
            conv_dw(128, 256, 2),  ## ->28
            conv_dw(256, 256, 1),
            conv_dw(256, 512, 1),  ## ->14
            conv_dw(512, 512, 1),
            conv_dw(512, 512, 1),
            conv_dw(512, 512, 1),
            conv_dw(512, 512, 1),
            conv_dw(512, 512, 1),
            conv_dw(512, 1024, 2),  ## ->7
            conv_dw(1024, 1024, 1),
        )
        self.avg_pool = nn.AvgPool2d(14) ## ->(512,1,1)
        self.classifier_cls = nn.Sequential(
            nn.Conv2d(1024, 1024, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(1024, 1024, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(1024, 1000, kernel_size=1, padding=0),
            nn.ReLU(inplace=True),  
        )
        self.classifier_loc = nn.Sequential( 
            nn.Conv2d(512, 1000, kernel_size=3, padding=1),
            nn.Sigmoid(),
        ) 
        self._initialize_weights()
        self.classifier_cls_copy = copy.deepcopy(self.classifier_cls)
        self.erase_branch = copy.deepcopy(self.model[-2:])

    def forward(self, x, label=None,N=1):

        batch = x.size(0)
        x = self.model[:-2](x)
        x_4 = x.clone()
        x = self.model[-2:](x)
        x = self.classifier_cls(x)
        self.feature_map = x

## score
        x = self.avg_pool(x).view(x.size(0), -1)
        self.score_1 = x    

# p_label 
        if N == 1:
            p_label = label.unsqueeze(-1)
        else:
            _, p_label = self.score_1.topk(N, 1, True, True)

## x_saliency    
        x_saliency_all = self.classifier_loc(x_4)
        x_saliency =  torch.zeros(batch, 1, 28, 28).cuda()
        for i in range(batch):
            x_saliency[i][0] = x_saliency_all[i][p_label[i]].mean(0)
        self.x_saliency = x_saliency

        return self.score_1

    def normalize_atten_maps(self, atten_maps):
        atten_shape = atten_maps.size()

        #--------------------------
        batch_mins, _ = torch.min(atten_maps.view(atten_shape[0:-2] + (-1,)), dim=-1, keepdim=True)
        batch_maxs, _ = torch.max(atten_maps.view(atten_shape[0:-2] + (-1,)), dim=-1, keepdim=True)
        atten_normed = torch.div(atten_maps.view(atten_shape[0:-2] + (-1,))-batch_mins,
                                 batch_maxs - batch_mins + 1e-10)
        atten_normed = atten_normed.view(atten_shape)

        return atten_normed

            
    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.xavier_uniform_(m.weight.data)
                if m.bias is not None:
                    m.bias.data.zero_()
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()
            elif isinstance(m, nn.Linear):
                m.weight.data.normal_(0, 0.01)
                m.bias.data.zero_()



def model(args, pretrained=True):
    # base and dilation can be modified according to your needs
    model = Model(args)
    if pretrained:
        pretrained_dict = torch.load('mobilenet_v1_with_relu_69_5.pth')
        model_dict = model.state_dict() ## 存储网络结构名字和对应的参数(字典)
        model_conv_name = []

        for i, (k, v) in enumerate(model_dict.items()):
            if 'tracked' in k[-7:]:
                continue
            model_conv_name.append(k)
        for i, (k, v) in enumerate(pretrained_dict.items()):
            model_dict[model_conv_name[i]] = v 
        model.load_state_dict(model_dict)
        print("pretrained weight load complete..")
    return model