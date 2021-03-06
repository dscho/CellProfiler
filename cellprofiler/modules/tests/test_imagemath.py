'''test_imagemath.py - test the ImageMath module
CellProfiler is distributed under the GNU General Public License.
See the accompanying file LICENSE for details.

Copyright (c) 2003-2009 Massachusetts Institute of Technology
Copyright (c) 2009-2013 Broad Institute
All rights reserved.

Please see the AUTHORS file for credits.

Website: http://www.cellprofiler.org
'''
__version__="$Revision$"

import base64
from matplotlib.image import pil_to_array
import numpy as np
import os
import PIL.Image as PILImage
import scipy.ndimage
from StringIO import StringIO
import unittest
import zlib

from cellprofiler.preferences import set_headless
set_headless()

import cellprofiler.pipeline as cpp
import cellprofiler.cpmodule as cpm
import cellprofiler.cpimage as cpi
import cellprofiler.measurements as cpmeas
import cellprofiler.objects as cpo
import cellprofiler.workspace as cpw

import cellprofiler.modules.imagemath as I

MEASUREMENT_NAME = 'mymeasurement'

class TestImageMath(unittest.TestCase):
    def test_01_000_load_subtract(self):
        data = r"""CellProfiler Pipeline: http://www.cellprofiler.org
Version:1
SVNRevision:8925
FromMatlab:True

Subtract:[module_num:1|svn_version:\'8913\'|variable_revision_number:3|show_window:False|notes:\x5B\x5D]
    Subtract this image\x3A:MySubtrahend
    From this image\x3A:MyMinuend
    What do you want to call the resulting image?:MyOutput
    Enter the factor to multiply the first image by before subtracting\x3A:1.5
    Enter the factor to multiply the second image by before subtracting\x3A:2.6
    Do you want negative values in the image to be set to zero?:Yes
    """
        pipeline = cpp.Pipeline()
        def callback(caller, event):
            self.assertFalse(isinstance(event, cpp.LoadExceptionEvent))
        pipeline.add_listener(callback)
        pipeline.load(StringIO(data))
        self.assertEqual(len(pipeline.modules()), 1)
        module = pipeline.modules()[0]
        self.assertTrue(isinstance(module, I.ImageMath))
        self.assertEqual(len(module.images), 2)
        self.assertEqual(module.images[0].image_name, "MyMinuend")
        self.assertEqual(module.images[1].image_name, "MySubtrahend")
        self.assertEqual(module.output_image_name, "MyOutput")
        self.assertEqual(module.operation, I.O_SUBTRACT)
        self.assertAlmostEqual(module.images[0].factor.value, 2.6)
        self.assertAlmostEqual(module.images[1].factor.value, 1.5)
        self.assertTrue(module.truncate_low)
        self.assertFalse(module.truncate_high)
        
    def test_01_001_load_combine(self):
        data = r"""CellProfiler Pipeline: http://www.cellprofiler.org
Version:1
SVNRevision:8925
FromMatlab:True

Combine:[module_num:1|svn_version:\'8913\'|variable_revision_number:3|show_window:False|notes:\x5B\x5D]
    What did you call the first image to be combined?:MyFirstImage
    What did you call the second image to be combined?:MySecondImage
    What did you call the third image to be combined?:Do not use
    What do you want to call the combined image?:MyOutputImage
    Enter the weight you want to give the first image:0.2
    Enter the weight you want to give the second image:0.7
    Enter the weight you want to give the third image:.10
    """
        pipeline = cpp.Pipeline()
        def callback(caller, event):
            self.assertFalse(isinstance(event, cpp.LoadExceptionEvent))
        pipeline.add_listener(callback)
        pipeline.load(StringIO(data))
        self.assertEqual(len(pipeline.modules()), 1)
        module = pipeline.modules()[0]
        self.assertTrue(isinstance(module, I.ImageMath))
        self.assertEqual(len(module.images), 2)
        self.assertEqual(module.images[0].image_name, "MyFirstImage")
        self.assertEqual(module.images[1].image_name, "MySecondImage")
        self.assertAlmostEqual(module.images[0].factor.value,0.2)
        self.assertAlmostEqual(module.images[1].factor.value,0.7)
        self.assertAlmostEqual(module.after_factor.value, 1.0/0.9)
        self.assertEqual(module.operation.value, I.O_ADD)
        self.assertEqual(module.output_image_name, "MyOutputImage")
    
    def test_01_002_load_invert_intensity(self):
        data = r"""CellProfiler Pipeline: http://www.cellprofiler.org
Version:1
SVNRevision:8925
FromMatlab:True

InvertIntensity:[module_num:1|svn_version:\'8913\'|variable_revision_number:1|show_window:False|notes:\x5B\x5D]
    What did you call the image to be inverted (made negative)?:MyImage
    What do you want to call the inverted image?:MyInvertedImage
"""
        pipeline = cpp.Pipeline()
        def callback(caller, event):
            self.assertFalse(isinstance(event, cpp.LoadExceptionEvent))
        pipeline.add_listener(callback)
        pipeline.load(StringIO(data))
        self.assertEqual(len(pipeline.modules()), 1)
        module = pipeline.modules()[0]
        self.assertTrue(isinstance(module, I.ImageMath))
        self.assertEqual(len(module.images), 2) # there are two, but only 1 shown
        self.assertEqual(module.images[0].image_name, "MyImage")
        self.assertEqual(module.output_image_name, "MyInvertedImage")
        self.assertEqual(module.operation, I.O_INVERT)
    
    def test_01_003_load_multiply(self):
        data = r"""CellProfiler Pipeline: http://www.cellprofiler.org
Version:1
SVNRevision:8925
FromMatlab:True

Multiply:[module_num:1|svn_version:\'8913\'|variable_revision_number:1|show_window:False|notes:\x5B\x5D]
    What is the name of the first image you would like to use:MyFirstImage
    What is the name of the second image you would like to use:MySecondImage
    What do you want to call the resulting image?:MyOutputImage
"""
        pipeline = cpp.Pipeline()
        def callback(caller, event):
            self.assertFalse(isinstance(event, cpp.LoadExceptionEvent))
        pipeline.add_listener(callback)
        pipeline.load(StringIO(data))
        self.assertEqual(len(pipeline.modules()), 1)
        module = pipeline.modules()[0]
        self.assertTrue(isinstance(module, I.ImageMath))
        self.assertEqual(len(module.images), 2)
        self.assertEqual(module.images[0].image_name, "MyFirstImage")
        self.assertEqual(module.images[1].image_name, "MySecondImage")
        self.assertEqual(module.images[0].factor, 1)
        self.assertEqual(module.images[1].factor, 1)
        self.assertEqual(module.output_image_name, "MyOutputImage")
        
    def test_01_01_load_matlab(self):
        data = ('eJzzdQzxcXRSMNUzUPB1DNFNy8xJ1VEIyEksScsvyrVSCHAO9/TTUXAuSk0s'
                'SU1RyM+zUgjJKFXwKs1RMDQDIitDCytjMwUjAwNLBZIBA6OnLz8DA0MWEwND'
                'xZy3EXfzLhuIlG1aIr0i5HaehJD4zidt9RN25EQ4dh+5lTVbTbHwsVleumbn'
                '4iMro+Z1HH9QWMHzZtKWzqkm9ryKHDGRFwvPfa+1O26/8TYzQ48804XE88ph'
                'qR9Wr1ioe1Rr+3rBpTdm/tYKOBB549/cq9EvEi02XtDdwvSk2bfzFm+6W17Y'
                'u2dXVQ2ZuXkXypanpUrcEH7yc3EkC098/0ehyOs/tJlOCu2MXcj6zbDQqeaE'
                '/ra8Ek7Rkuo1u/i3VU5osdFYM+/YrZ318jl/p07ZI3v8T//hquZpX162q84J'
                'OttWUnW8Mu7JBxmVCr4DCSuazR5NYfFjZK7NebN4+vT71U51O2v3LTqydUF+'
                '+9vST1t070fuKLe0CO2YfvvXFN3XXYV1Mr1cL8tYYvOkzzFVbpm1Lm9Wawk/'
                'a2zefOHqJtkrL/5MELIRqrgZNGfG8++/Qhf/rdmaXrO/+t910eevbb/+stzx'
                '22nOHTmBs4oh3H8+ON9K2ZP/b2PFfbM14SV2na9/G1tzix48yTmHpy3Ffm8d'
                '37p1H3O894hb7hBWjMtLPn6EO4ftwqUNvM9nB2dP/FPKape32bjJbvGJ3S1f'
                '1mn4+z94uO2gtXDyqsnLX+1w+dhxftPrF5Fs/hdrls4VfyYX8zM4Y6HIvk1/'
                'z86KD/356tzyG/bPLe+c/O57t/Z91/nHRo8nbKtfI37xjnLj7bh5276t1py3'
                'pfrzNPfkaKWi/8d2nOqrv7Z53R/Rq7/X/0//fdNsHrdm9f5pDp/qF6x6/Ui4'
                'cZmg9YeQv+/WWS467Odd+ej+ZT8/u9S0uWW77+56J+r6JSRy2tHqUjk/ztv7'
                'beq2/Cv8wx+Qd8/m5kP5qdt+/WfJeirzEgCAxWF+')
        pipeline = cpp.Pipeline()
        def callback(caller,event):
            self.assertFalse(isinstance(event, cpp.LoadExceptionEvent))
        pipeline.add_listener(callback)
        pipeline.load(StringIO(zlib.decompress(base64.b64decode(data))))
        #
        # There are 3 ImageMath modules:
        # 1)
        #   image_name[0] = DNA, factor[0] = 1, operation = invert, truncation
        #   output_image_name = DNAAfterMath
        # 2)
        #   image_name[0] = DNA, factor[0] = 1
        #   image_name[1] = Cytoplasm, factor[1] = 2
        #   operation = add, exponent = 4, multiply = 5, no truncation
        #   output_image_name = ImageAfterMath
        # 3)  DNA, Cytoplasm, Actin
        self.assertEqual(len(pipeline.modules()), 4)
        module = pipeline.modules()[1]
        self.assertTrue(isinstance(module, I.ImageMath))
        self.assertEqual(len(module.images), 2)
        self.assertEqual(module.images[0].image_name.value, 'DNA')
        self.assertEqual(module.output_image_name.value, 'DNAAfterMath')
        self.assertEqual(module.operation.value, I.O_INVERT)
        self.assertTrue(module.truncate_low.value)
        self.assertTrue(module.truncate_high.value)
        
        module = pipeline.modules()[2]
        self.assertTrue(isinstance(module, I.ImageMath))
        self.assertEqual(len(module.images), 2)
        self.assertEqual(module.images[0].image_name.value, 'DNA')
        self.assertEqual(module.images[0].factor.value, 1)
        self.assertEqual(module.images[1].image_name.value, 'Cytoplasm')
        self.assertEqual(module.images[1].factor.value, 2)
        self.assertEqual(module.output_image_name.value, 'ImageAfterMath')
        self.assertEqual(module.operation.value, I.O_ADD)
        self.assertEqual(module.exponent.value, 4)
        self.assertEqual(module.after_factor.value, 5)
        self.assertFalse(module.truncate_low.value)
        self.assertFalse(module.truncate_high.value)
        
        module = pipeline.modules()[3]
        self.assertTrue(isinstance(module, I.ImageMath))
        self.assertEqual(len(module.images), 3)
        self.assertEqual(module.images[0].image_name.value, 'DNA')
        self.assertEqual(module.images[1].image_name.value, 'Cytoplasm')
        self.assertEqual(module.images[2].image_name.value, 'Actin')
        self.assertEqual(module.output_image_name.value, 'ImageAfterMath')
        self.assertEqual(module.operation.value, I.O_ADD)
    
    def test_01_02_load_wierd_matlab(self):
        '''Load some ImageMath modules with constants typed in instead of images'''
        data = ('eJzzdQzxcXRSMNUzUPB1DNFNy8xJ1VEIyEksScsvyrVSCHAO9/TTUXAuSk0s'
                'SU1RyM+zUgjJKFXwKs1RMDQDIisTSysTMwUjAwNLBZIBA6OnLz8DA8M2JgaG'
                'ijlvIvzzbxmI1C88cCNk4brdOZf4LN9teuevbz1pmq+rVMDW0KWeuyWSDgQJ'
                'uXcGH7S72/eb47dFt2LjEe5ez5NebnKb1jz/8f1z9flzj4/6MvxYynTl776H'
                '27l0loi98FpS+FfK2G3NxuhmrT08x+p/vRWzZOHlqenm4d+9YUrBnuTeF2fP'
                'xNm9CrprXMA/8+LJfV9sihtkt9tzNR587G109Jjpz0ZFvYdbtGvcY5zWMsh/'
                '6F58ulRT+FruL9/ajV3NSkca++Xdj/38I7bmWbjwozKRmfUiW6RtUvPt/S9O'
                'WKmWdJjzeeX8Q8UCjy0byvybhbZLRD9cdeGanrWRhWpb8APmhitVtw/VnpEM'
                'n/L3ttm7YK51Yod1S3JfLDc+uSMs6QfXnDlpt/v1/9apzVn2OqjOTOHdc5v8'
                'auZnPyLVtfe9luy5ccyHLV78Q0z+ZOtFyRM2/e9seP7L0pT9yKGgyu8rgeyf'
                'PYG3HdZJ9ogr+r/R8rOZnn7rqt+tndo79ny+tO7Hz/WFa0XuGCuui8kPvrrI'
                '5+udBRN0Ju1PrfkuXa7VKfz5s/n/aHX/ORHiX188vnHT62Du6z3vsmv0gwrO'
                't/4omhthtf6PTcqKIy6Pn4ZvP1Mny1UT8z27NvfIhsuuOUqnL4tU7Lj38JjL'
                'jH/p89Y81+7Jj9qfKWc98Qnv7y0WKld/J7OfvaNoVMB03/lv5Pe6nG77938F'
                '3m6/t7D3h3rv7/cnF71/q/Z7xpT5zz2T3wSc16tMqSy7uq72qecu9riPK/7F'
                'q2zrfhEeWGn29vK1qXfvr3k9/dvT7PvJv0M/3Tn/OToyPl9DYH/+uVnq+4KW'
                'lCvJa0S+Pmfp/qMw6JPHR5f37q85bS7+Xcvy66Pi9Pa7+1Mit4c9/LT9f2ZF'
                'nvj67v3767b+af0Xn1Ox7/6BXz8Xnjj3n5mB4f//5AYmN42z7EekHM6wHZHx'
                'eLQm4F9COD8Dk26hOwCE1ox/')
        pipeline = cpp.Pipeline()
        def callback(caller,event):
            self.assertFalse(isinstance(event, cpp.LoadExceptionEvent))
        pipeline.add_listener(callback)
        pipeline.load(StringIO(zlib.decompress(base64.b64decode(data))))
        #
        # Modules:        
        # 1) Add, 1
        # 2) Subtract, 1
        # 3) Multiply, 2
        # 4) Divide, 2
        # 5) Combine, .3
        self.assertEqual(len(pipeline.modules()), 6)
        for i in range(1,5):
            module = pipeline.modules()[i]
            self.assertEqual(len(module.images), 2)
            self.assertEqual(module.operation.value, I.O_NONE)
        self.assertEqual(pipeline.modules()[1].addend.value, 1)
        self.assertEqual(pipeline.modules()[2].addend.value, -1)
        self.assertAlmostEqual(pipeline.modules()[3].after_factor.value, 2)
        self.assertAlmostEqual(pipeline.modules()[4].after_factor.value, .5)
        module = pipeline.modules()[5]
        self.assertEqual(len(module.images),2)
        self.assertAlmostEqual(module.addend.value, .3)
    
    def run_imagemath(self, images, modify_module_fn=None, measurement = None):
        '''Run the ImageMath module, returning the image created
        
        images - a list of dictionaries. The dictionary has keys:
                 pixel_data - image pixel data
                 mask - mask for image
                 cropping - cropping mask for image
        modify_module_fn - a function of the signature, fn(module)
                 that allows the test to modify the module.
        measurement - an image measurement value
        '''
        image_set_list = cpi.ImageSetList()
        image_set = image_set_list.get_image_set(0)
        module = I.ImageMath()
        module.module_num = 1
        for i,image in enumerate(images):
            pixel_data = image['pixel_data']
            mask = image.get('mask', None)
            cropping = image.get('cropping', None)
            if i >= 2:
                module.add_image()
            name = 'inputimage%s'%i
            module.images[i].image_name.value = name
            img = cpi.Image(pixel_data, mask=mask, crop_mask=cropping)
            image_set.add(name, img)
        module.output_image_name.value = 'outputimage'
        if modify_module_fn is not None:
            modify_module_fn(module)
        pipeline = cpp.Pipeline()
        pipeline.add_module(module)
        measurements = cpmeas.Measurements()
        if measurement is not None:
            measurements.add_image_measurement(MEASUREMENT_NAME, measurement)
        workspace = cpw.Workspace(pipeline, module, image_set, cpo.ObjectSet(),
                                  measurements, image_set_list)
        module.run(workspace)
        return image_set.get_image('outputimage')
    
    def check_expected(self, image, expected, mask=None, ignore=False):
        if mask is None and not image.has_crop_mask:
            self.assertTrue(np.all(np.abs(image.pixel_data - expected <
                                          np.sqrt(np.finfo(np.float32).eps))))
            self.assertFalse(image.has_mask)
        elif mask is not None and ignore==True:
            self.assertTrue(np.all(np.abs(image.pixel_data - expected <
                                          np.sqrt(np.finfo(np.float32).eps))))
            self.assertTrue(image.has_mask)
        elif mask is not None and ignore==False:
            self.assertTrue(image.has_mask)
            if not image.has_crop_mask:
                self.assertTrue(np.all(mask == image.mask))
            self.assertTrue(np.all(np.abs(image.pixel_data[image.mask] - 
                                          expected[image.mask]) <
                                          np.sqrt(np.finfo(np.float32).eps)))
        
    def test_02_01_exponent(self):
        '''Test exponentiation of an image'''
        def fn(module):
            module.exponent.value = 2
            module.operation.value = I.O_NONE
        
        np.random.seed(0)
        image = np.random.uniform(size=(10,10)).astype(np.float32)
        expected = image**2
        output = self.run_imagemath([{ 'pixel_data': image}], fn)
        self.check_expected(output, expected)

    def test_02_02_factor(self):
        '''Test multiplicative factor'''
        def fn(module):
            module.after_factor.value = .5
            module.operation.value = I.O_NONE
        
        np.random.seed(0)
        image = np.random.uniform(size=(10,10))
        expected = image*.5
        output = self.run_imagemath([{ 'pixel_data': image}], fn)
        self.check_expected(output, expected)
    
    def test_02_03_addend(self):
        '''Test adding a value to image'''
        def fn(module):
            module.addend.value = .5
            module.operation.value = I.O_NONE
        
        np.random.seed(0)
        image = np.random.uniform(size=(10,10))*.5
        image = image.astype(np.float32)
        expected = image + .5
        output = self.run_imagemath([{ 'pixel_data': image}], fn)
        self.check_expected(output, expected)
    
    def test_02_04_mask(self):
        '''Test a mask in the first image'''
        def fn(module):
            module.operation.value = I.O_NONE
        np.random.seed(0)
        image = np.random.uniform(size=(10,10)).astype(np.float32)
        mask = np.random.uniform(size=(10,10)) > .3
        output = self.run_imagemath([{'pixel_data': image,
                                      'mask': mask
                                      }], fn)
        self.check_expected(output, image, mask)
    
    def test_03_01_add(self):
        '''Test adding'''
        def fn(module):
            module.operation.value = I.O_ADD
            module.truncate_high.value = False
        np.random.seed(0)
        for n in range(2,5):
            images = [{ 'pixel_data':np.random.uniform(size=(10,10)).astype(np.float32) }
                      for i in range(n)]
            expected = reduce(np.add,[x['pixel_data'] for x in images])
            output = self.run_imagemath(images, fn)
            self.check_expected(output, expected)
    
    def test_03_02_add_mask(self):
        '''Test adding masked images'''
        '''Test adding'''
        def fn(module):
            module.operation.value = I.O_ADD
            module.truncate_high.value = False
        np.random.seed(0)
        for n in range(2,5):
            images = [{ 'pixel_data':np.random.uniform(size=(50,50)).astype(np.float32),
                        'mask': (np.random.uniform(size=(50,50))>.1) }
                      for i in range(n)]
            expected = reduce(np.add,[x['pixel_data'] for x in images])
            mask = reduce(np.logical_and, [x['mask'] for x in images])
            output = self.run_imagemath(images, fn)
            self.check_expected(output, expected, mask)
    
    def test_03_03_add_mask_truncate(self):
        def fn(module):
            module.operation.value = I.O_ADD
            module.truncate_high.value = True
        np.random.seed(0)
        for n in range(2,5):
            images = [{ 'pixel_data':np.random.uniform(size=(50,50)).astype(np.float32),
                        'mask': (np.random.uniform(size=(50,50))>.1) }
                      for i in range(n)]
            expected = reduce(np.add,[x['pixel_data'] for x in images])
            expected[expected>1] = 1
            mask = reduce(np.logical_and, [x['mask'] for x in images])
            output = self.run_imagemath(images, fn)
            self.check_expected(output, expected, mask)
    
    def test_03_04_add_crop(self):
        '''Add images, cropping to border'''
        def fn(module):
            module.operation.value = I.O_ADD
            module.truncate_high.value = False
        np.random.seed(0)
        crop_mask = np.zeros((20,20), bool)
        crop_mask[5:15,5:15] = True
        for n in range(2,3):
            for m in range(n):
                images = [{ 'pixel_data':np.random.uniform(size=(20,20)).astype(np.float32) }
                          for i in range(n)]
                for i,img in enumerate(images):
                    img['cropped_data'] = img['pixel_data'][5:15,5:15]
                    if m == i:
                        img['pixel_data'] = img['cropped_data']
                        img['cropping'] = crop_mask
                expected = reduce(np.add,[x['cropped_data'] for x in images])
                output = self.run_imagemath(images, fn)
                self.check_expected(output, expected)
    
    def test_03_05_add_factors(self):
        '''Test adding with factors'''
        np.random.seed(0)
        for n in range(2,5):
            images = [{ 'pixel_data':np.random.uniform(size=(10,10)).astype(np.float32) }
                      for i in range(n)]
            factors = np.random.uniform(size=n)
            expected = reduce(np.add,[x['pixel_data'] * factor 
                                      for x,factor in zip(images,factors)])
            def fn(module):
                module.operation.value = I.O_ADD
                module.truncate_high.value = False
                for i in range(n):
                    module.images[i].factor.value = factors[i]
            output = self.run_imagemath(images, fn)
            self.check_expected(output, expected)
    
    def test_03_06_ignore_mask(self):
        '''Test adding images with masks, but ignoring the masks'''
        def fn(module):
            module.operation.value = I.O_ADD
            module.truncate_high.value = False
            module.ignore_mask.value = True
        np.random.seed(0)
        for n in range(2,5):
            images = [{ 'pixel_data':np.random.uniform(size=(50,50)).astype(np.float32),
                        'mask': (np.random.uniform(size=(50,50))>.1) }
                      for i in range(n)]
            expected = reduce(np.add,[x['pixel_data'] for x in images])
            mask = reduce(np.logical_and, [x['mask'] for x in images])
            output = self.run_imagemath(images, fn)
            self.check_expected(output, expected, mask, True)
        
    def test_04_01_subtract(self):
        '''Test subtracting'''
        def fn(module):
            module.operation.value = I.O_SUBTRACT
            module.truncate_low.value = False
        np.random.seed(0)
        for n in range(2,5):
            images = [{ 'pixel_data':np.random.uniform(size=(10,10)).astype(np.float32) }
                      for i in range(n)]
            expected = reduce(np.subtract,[x['pixel_data'] for x in images])
            output = self.run_imagemath(images, fn)
            self.check_expected(output, expected)

    def test_04_02_subtract_truncate(self):
        '''Test subtracting with truncation'''
        def fn(module):
            module.operation.value = I.O_SUBTRACT
            module.truncate_low.value = True
        np.random.seed(0)
        for n in range(2,5):
            images = [{ 'pixel_data':np.random.uniform(size=(10,10)).astype(np.float32) }
                      for i in range(n)]
            expected = reduce(np.subtract,[x['pixel_data'] for x in images])
            expected[expected<0] = 0
            output = self.run_imagemath(images, fn)
            self.check_expected(output, expected)

    def test_05_01_multiply(self):
        def fn(module):
            module.operation.value = I.O_MULTIPLY
            module.truncate_low.value = False
        np.random.seed(0)
        for n in range(2,5):
            images = [{ 'pixel_data':np.random.uniform(size=(10,10)).astype(np.float32) }
                      for i in range(n)]
            expected = reduce(np.multiply,[x['pixel_data'] for x in images])
            output = self.run_imagemath(images, fn)
            self.check_expected(output, expected)

    def test_06_01_divide(self):
        def fn(module):
            module.operation.value = I.O_DIVIDE
            module.truncate_low.value = False
        np.random.seed(0)
        for n in range(2,5):
            images = [{ 'pixel_data':np.random.uniform(size=(10,10)).astype(np.float32) }
                      for i in range(n)]
            expected = reduce(np.divide,[x['pixel_data'] for x in images])
            output = self.run_imagemath(images, fn)
            self.check_expected(output, expected)
    
    def test_07_01_average(self):
        def fn(module):
            module.operation.value = I.O_AVERAGE
            module.truncate_low.value = False
        np.random.seed(0)
        for n in range(2,5):
            images = [{ 'pixel_data':np.random.uniform(size=(10,10)).astype(np.float32) }
                      for i in range(n)]
            expected = reduce(np.add,[x['pixel_data'] for x in images]) / n
            output = self.run_imagemath(images, fn)
            self.check_expected(output, expected)

    def test_07_02_average_factors(self):
        '''Test averaging with factors'''
        np.random.seed(0)
        for n in range(2,5):
            images = [{ 'pixel_data':np.random.uniform(size=(10,10)).astype(np.float32) }
                      for i in range(n)]
            factors = np.random.uniform(size=n)
            expected = reduce(np.add,[x['pixel_data'] * factor 
                                      for x,factor in zip(images,factors)])
            expected /= np.sum(factors)
            def fn(module):
                module.operation.value = I.O_AVERAGE
                module.truncate_high.value = False
                for i in range(n):
                    module.images[i].factor.value = factors[i]
            output = self.run_imagemath(images, fn)
            self.check_expected(output, expected)
    
    def test_08_01_invert(self):
        '''Test invert of an image'''
        def fn(module):
            module.operation.value = I.O_INVERT
        
        np.random.seed(0)
        image = np.random.uniform(size=(10,10)).astype(np.float32)
        expected = 1-image
        output = self.run_imagemath([{ 'pixel_data': image}], fn)
        self.check_expected(output, expected)

    def test_09_01_log_transform(self):
        '''Test log transform of an image'''
        def fn(module):
            module.operation.value = I.O_LOG_TRANSFORM
            module.truncate_low.value = False
        
        np.random.seed(0)
        image = np.random.uniform(size=(10,10)).astype(np.float32)
        expected = np.log2(image)
        output = self.run_imagemath([{ 'pixel_data': image}], fn)
        self.check_expected(output, expected)
        
    def test_10_01_with_measurement(self):
        '''Test multiplying an image by a measurement'''
        def fn(module):
            module.operation.value = I.O_MULTIPLY
            module.images[1].image_or_measurement.value = I.IM_MEASUREMENT
            module.images[1].measurement.value = MEASUREMENT_NAME

        np.random.seed(101)
        measurement = 1.23
        expected = np.random.uniform(size=(10,20)).astype(np.float32) 
        image = expected / measurement
        output = self.run_imagemath([{ 'pixel_data':image }],
                                    modify_module_fn = fn, 
                                    measurement = measurement)
        self.check_expected(output, expected)

    def test_10_02_with_measurement_and_mask(self):
        '''Test a measurement operation on a masked image'''
        def fn(module):
            module.operation.value = I.O_MULTIPLY
            module.images[1].image_or_measurement.value = I.IM_MEASUREMENT
            module.images[1].measurement.value = MEASUREMENT_NAME

        np.random.seed(102)
        measurement = 1.52
        expected = np.random.uniform(size=(10,20)).astype(np.float32) 
        image = expected / measurement
        mask = np.random.uniform(size=(10,20)) < .2
        output = self.run_imagemath([{ 'pixel_data':image, 'mask':mask }],
                                    modify_module_fn = fn, 
                                    measurement = measurement)
        self.check_expected(output, expected, mask)
        
