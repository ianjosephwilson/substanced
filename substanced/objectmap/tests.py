import sys
import unittest
from zope.interface import implementer

from pyramid import testing

IS_32_BIT = sys.maxsize == 2**32

class TestObjectMap(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self, family=None):
        from . import ObjectMap
        return ObjectMap(family=family)

    def test_ctor_alternate_family(self):
        import BTrees
        inst = self._makeOne(family=BTrees.family32)
        self.assertEqual(inst.family, BTrees.family32)

    def test_new_objectid_empty(self):
        inst = self._makeOne()
        times = [0]
        def randrange(frm, to):
            val = times[0]
            times[0] = times[0] + 1
            return val
        inst._randrange = randrange
        result = inst.new_objectid()
        # cant get 0 back, it's irresolveable
        self.assertEqual(result, 1)
        
    def test_new_objectid_notempty(self):
        inst = self._makeOne()
        times = [0]
        def randrange(frm, to):
            val = times[0]
            times[0] = times[0] + 1
            return val
        inst._randrange = randrange
        inst.objectid_to_path[1] = True
        result = inst.new_objectid()
        self.assertEqual(result, 2)

    def test_new_objectid_gt_maxint(self):
        inst = self._makeOne()
        oob = inst.family.maxint + 1
        times = [oob, 5]
        def randrange(frm, to):
            val = times.pop(0)
            return val
        inst._randrange = randrange
        result = inst.new_objectid()
        self.assertEqual(result, 5)

    def test_objectid_for_object(self):
        obj = testing.DummyResource()
        inst = self._makeOne()
        inst.path_to_objectid[(u'',)] = 1
        self.assertEqual(inst.objectid_for(obj), 1)

    def test_objectid_for_path_tuple(self):
        inst = self._makeOne()
        inst.path_to_objectid[(u'',)] = 1
        self.assertEqual(inst.objectid_for((u'',)), 1)

    def test_objectid_for_nonsense(self):
        inst = self._makeOne()
        self.assertRaises(ValueError, inst.objectid_for, 'a')

    def test_path_for(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = 'abc'
        self.assertEqual(inst.path_for(1), 'abc')

    def test_object_for_int(self):
        a = testing.DummyResource()
        inst = self._makeOne()
        inst.objectid_to_path[1] = 'abc'
        inst._find_resource = lambda *arg: a
        self.assertEqual(inst.object_for(1), a)

    if IS_32_BIT: # pragma: no cover
        def test_object_for_long(self):
            a = testing.DummyResource()
            inst = self._makeOne()
            oid = sys.maxint + 1
            inst.objectid_to_path[oid] = 'abc'
            inst._find_resource = lambda *arg: a
            self.assertEqual(inst.object_for(oid), a)

    def test_object_for_path_tuple(self):
        a = testing.DummyResource()
        inst = self._makeOne()
        inst.objectid_to_path[1] = 'abc'
        inst._find_resource = lambda *arg: a
        self.assertEqual(inst.object_for((u'',)), a)

    def test_object_for_unknown(self):
        inst = self._makeOne()
        self.assertRaises(ValueError, inst.object_for, None)

    def test_object_for_cantbefound(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = 'abc'
        def find_resource(*arg):
            raise KeyError('a')
        inst._find_resource = find_resource
        self.assertEqual(inst.object_for(1), None)
        
    def test_object_for_path_tuple_alternate_context(self):
        a = testing.DummyResource()
        inst = self._makeOne()
        inst.objectid_to_path[1] = 'abc'
        L= []
        def find_resource(context, path_tuple):
            L.append(context)
            return a
        inst._find_resource = find_resource
        self.assertEqual(inst.object_for((u'',), 'a'), a)
        self.assertEqual(L, ['a'])

    def test__find_resource_no_context(self):
        self.config.testing_resources({'/a':1})
        inst = self._makeOne()
        inst.__parent__ = None
        self.assertEqual(inst._find_resource(None, ('', 'a')), 1)

    def test__find_resource_with_alternate_context(self):
        self.config.testing_resources({'/a':1})
        inst = self._makeOne()
        ctx = testing.DummyResource()
        self.assertEqual(inst._find_resource(ctx, ('', 'a')), 1)
        
    def test_add_already_in_path_to_objectid(self):
        inst = self._makeOne()
        obj = testing.DummyResource()
        obj.__objectid__ = 1
        inst.path_to_objectid[(u'',)] = 1
        self.assertRaises(ValueError, inst.add, obj, (u'',))

    def test_add_duplicating(self):
        inst = self._makeOne()
        obj = testing.DummyResource()
        obj.__objectid__ = 1
        inst.path_to_objectid[(u'',)] = 1
        self.assertRaises(ValueError, inst.add, obj, (u'',), True)

    def test_add_already_in_objectid_to_path(self):
        inst = self._makeOne()
        obj = testing.DummyResource()
        obj.__objectid__ = 1
        inst.objectid_to_path[1] = True
        self.assertRaises(ValueError, inst.add, obj, (u'',))

    def test_add_not_a_path_tuple(self):
        inst = self._makeOne()
        self.assertRaises(ValueError, inst.add, None, None)

    def test_add_traversable_object(self):
        inst = self._makeOne()
        inst._v_nextid = 1
        obj = testing.DummyResource()
        inst.add(obj, (u'',))
        self.assertEqual(inst.objectid_to_path[1], (u'',))
        self.assertEqual(obj.__objectid__, 1)
        
    def test_add_not_valid(self):
        inst = self._makeOne()
        self.assertRaises(AttributeError, inst.add, 'a', (u'',))

    def test_remove_not_an_int_or_tuple(self):
        inst = self._makeOne()
        self.assertRaises(ValueError, inst.remove, 'a')

    def test_remove_int(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        inst.path_to_objectid[(u'',)] = 1
        inst.pathindex[(u'',)] = {0:[1]}
        inst.remove(1)
        self.assertEqual(dict(inst.objectid_to_path), {})

    if IS_32_BIT: # pragma: no cover
        def test_remove_long(self):
            inst = self._makeOne()
            oid = sys.maxint + 1
            inst.objectid_to_path[oid] = (u'',)
            inst.path_to_objectid[(u'',)] = oid
            inst.pathindex[(u'',)] = {0:[oid]}
            inst.remove(oid)
            self.assertEqual(dict(inst.objectid_to_path), {})
        
    def test_remove_traversable_object(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        inst.path_to_objectid[(u'',)] = 1
        inst.pathindex[(u'',)] = {0:[1]}
        obj = testing.DummyResource()
        inst.remove(obj)
        self.assertEqual(dict(inst.objectid_to_path), {})
        
    def test_remove_no_omap(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        result = inst.remove((u'',))
        self.assertEqual(list(result), [])

    def test_pathlookup_not_valid(self):
        inst = self._makeOne()
        self.assertRaises(ValueError, inst.pathlookup, 1)

    def test_pathlookup_traversable_object(self):
        inst = self._makeOne()
        obj = testing.DummyResource()
        gen = inst.pathlookup(obj)
        result = list(gen)
        self.assertEqual(result, [])

    def test_navgen_notexist(self):
        inst = self._makeOne()
        result = inst.navgen((u'',), 99)
        self.assertEqual(result, [])

    def test_navgen_bigdepth(self):
        inst = self._makeOne()
        root = resource('/')
        a = resource('/a')
        ab = resource('/a/b')
        abc = resource('/a/b/c')
        z = resource('/z')
        for thing in root, a, ab, abc, z:
            inst.add(thing, thing.path_tuple)
        result = inst.navgen(root, 99)
        self.assertEqual(
            result, 
            [{'path': ('', u'a'), 
              'name':u'a',
              'children': [{'path': ('', u'a', u'b'), 
                            'name':u'b',
                            'children': [{'path': ('', u'a', u'b', u'c'), 
                                          'name':u'c',
                                          'children': []}]}]}, 
             {'path': ('', u'z'), 
              'name':u'z',
              'children': []}]
            )

    def test_navgen_bigdepth_notroot(self):
        inst = self._makeOne()
        root = resource('/')
        a = resource('/a')
        ab = resource('/a/b')
        abc = resource('/a/b/c')
        z = resource('/z')
        for thing in root, a, ab, abc, z:
            inst.add(thing, thing.path_tuple)
        result = inst.navgen(a, 99)
        self.assertEqual(
            result,
            [{'path': ('', u'a', u'b'), 
              'name':u'b',
              'children': [{'path': ('', u'a', u'b', u'c'), 
                            'name':u'c',
                            'children': []}]}]
            )
        
    def test_navgen_smalldepth(self):
        inst = self._makeOne()
        root = resource('/')
        a = resource('/a')
        ab = resource('/a/b')
        abc = resource('/a/b/c')
        z = resource('/z')
        for thing in root, a, ab, abc, z:
            inst.add(thing, thing.path_tuple)
        result = inst.navgen(root, 1)
        self.assertEqual(
            result,
            [{'path': ('', u'a'), 
              'name':'a',
              'children': []},
             {'path': ('', u'z'), 
              'name':u'z',
              'children': []}]
            )

    def test_navgen_smalldepth_notroot(self):
        inst = self._makeOne()
        root = resource('/')
        a = resource('/a')
        ab = resource('/a/b')
        abc = resource('/a/b/c')
        z = resource('/z')
        for thing in root, a, ab, abc, z:
            inst.add(thing, thing.path_tuple)
        result = inst.navgen(a, 1)
        self.assertEqual(
            result,
            [{'path': ('', u'a', u'b'), 
              'name':u'b',
              'children': []}]
            )
        
    def test_navgen_nodepth(self):
        inst = self._makeOne()
        root = resource('/')
        a = resource('/a')
        ab = resource('/a/b')
        abc = resource('/a/b/c')
        z = resource('/z')
        for thing in root, a, ab, abc, z:
            inst.add(thing, thing.path_tuple)
        result = inst.navgen(root, 0)
        self.assertEqual(result, [])

    def test_navgen_nodepth_notroot(self):
        inst = self._makeOne()
        root = resource('/')
        a = resource('/a')
        ab = resource('/a/b')
        abc = resource('/a/b/c')
        z = resource('/z')
        for thing in root, a, ab, abc, z:
            inst.add(thing, thing.path_tuple)
        result = inst.navgen(a, 0)
        self.assertEqual(result, [])
        
    def test_functional(self):

        def l(path, depth=None, include_origin=True):
            path_tuple = split(path)
            return sorted(
                list(objmap.pathlookup(path_tuple, depth, include_origin))
                )

        objmap = self._makeOne()
        objmap._v_nextid = 1

        root = resource('/')
        a = resource('/a')
        ab = resource('/a/b')
        abc = resource('/a/b/c')
        z = resource('/z')

        oid1 = objmap.add(ab, ab.path_tuple)
        oid2 = objmap.add(abc, abc.path_tuple)
        oid3 = objmap.add(a, a.path_tuple)
        oid4 = objmap.add(root, root.path_tuple)
        oid5 = objmap.add(z, z.path_tuple)

        # /
        nodepth = l('/')
        assert nodepth == [oid1, oid2, oid3, oid4, oid5], nodepth
        depth0 = l('/', depth=0)
        assert depth0 == [oid4], depth0
        depth1 = l('/', depth=1)
        assert depth1 == [oid3, oid4, oid5], depth1
        depth2 = l('/', depth=2)
        assert depth2 == [oid1, oid3, oid4, oid5], depth2
        depth3 = l('/', depth=3)
        assert depth3 == [oid1, oid2, oid3, oid4, oid5], depth3
        depth4 = l('/', depth=4)
        assert depth4 == [oid1, oid2, oid3, oid4, oid5], depth4

        # /a
        nodepth = l('/a')
        assert nodepth == [oid1, oid2, oid3], nodepth
        depth0 = l('/a', depth=0)
        assert depth0 == [oid3], depth0
        depth1 = l('/a', depth=1)
        assert depth1 == [oid1, oid3], depth1
        depth2 = l('/a', depth=2)
        assert depth2 == [oid1, oid2, oid3], depth2
        depth3 = l('/a', depth=3)
        assert depth3 == [oid1, oid2, oid3], depth3

        # /a/b
        nodepth = l('/a/b')
        assert nodepth == [oid1, oid2], nodepth
        depth0 = l('/a/b', depth=0)
        assert depth0 == [oid1], depth0
        depth1 = l('/a/b', depth=1)
        assert depth1 == [oid1, oid2], depth1
        depth2 = l('/a/b', depth=2)
        assert depth2 == [oid1, oid2], depth2

        # /a/b/c
        nodepth = l('/a/b/c')
        assert nodepth == [oid2], nodepth
        depth0 = l('/a/b/c', depth=0)
        assert depth0 == [oid2], depth0
        depth1 = l('/a/b/c', depth=1)
        assert depth1 == [oid2], depth1

        # remove '/a/b'
        removed = objmap.remove(oid1)
        assert removed == set([1,2])

        # /a/b/c
        nodepth = l('/a/b/c')
        assert nodepth == [], nodepth
        depth0 = l('/a/b/c', depth=0)
        assert depth0 == [], depth0
        depth1 = l('/a/b/c', depth=1)
        assert depth1 == [], depth1

        # /a/b
        nodepth = l('/a/b')
        assert nodepth == [], nodepth
        depth0 = l('/a/b', depth=0)
        assert depth0 == [], depth0
        depth1 = l('/a/b', depth=1)
        assert depth1 == [], depth1

        # /a
        nodepth = l('/a')
        assert nodepth == [oid3], nodepth
        depth0 = l('/a', depth=0)
        assert depth0 == [oid3], depth0
        depth1 = l('/a', depth=1)
        assert depth1 == [oid3], depth1

        # /
        nodepth = l('/')
        assert nodepth == [oid3, oid4, oid5], nodepth
        depth0 = l('/', depth=0)
        assert depth0 == [oid4], depth0
        depth1 = l('/', depth=1)
        assert depth1 == [oid3, oid4, oid5], depth1

        # test include_origin false with /, no depth
        nodepth = l('/', include_origin=False)
        assert nodepth == [oid3, oid5], nodepth

        # test include_origin false with /, depth=1
        depth1 = l('/', include_origin=False, depth=0)
        assert depth1 == [], depth1
        
        pathindex = objmap.pathindex
        keys = list(pathindex.keys())

        self.assertEqual(
            keys,
            [(u'',), (u'', u'a'), (u'', u'z')]
        )

        root = pathindex[(u'',)]
        self.assertEqual(len(root), 2)
        self.assertEqual(set(root[0]), set([4]))
        self.assertEqual(set(root[1]), set([3,5]))

        a = pathindex[(u'', u'a')]
        self.assertEqual(len(a), 1)
        self.assertEqual(set(a[0]), set([3]))

        z = pathindex[(u'', u'z')]
        self.assertEqual(len(z), 1)
        self.assertEqual(set(z[0]), set([5]))
        
        self.assertEqual(
            dict(objmap.objectid_to_path),
            {3: (u'', u'a'), 4: (u'',), 5: (u'', u'z')})
        self.assertEqual(
            dict(objmap.path_to_objectid),
            {(u'', u'z'): 5, (u'', u'a'): 3, (u'',): 4})

        # remove '/'
        removed = objmap.remove((u'',))
        self.assertEqual(removed, set([3,4,5]))

        assert dict(objmap.pathindex) == {}
        assert dict(objmap.objectid_to_path) == {}
        assert dict(objmap.path_to_objectid) == {}

    def test__refids_for_source_missing(self):
        inst = self._makeOne()
        self.assertRaises(ValueError, inst._refids_for, 1, 2)
        
    def test__refids_for_target_missing(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        self.assertRaises(ValueError, inst._refids_for, 1, 2)

    def test__refids_for_success_oids(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        inst.objectid_to_path[2] = (u'',)
        s, t = inst._refids_for(1, 2)
        self.assertEqual(s, 1)
        self.assertEqual(t, 2)

    def test__refids_for_success_objects(self):
        inst = self._makeOne()
        one = testing.DummyResource()
        one.__objectid__ = 1
        two = testing.DummyResource()
        two.__objectid__ = 2
        inst.objectid_to_path[1] = (u'',)
        inst.objectid_to_path[2] = (u'',)
        s, t = inst._refids_for(one, two)
        self.assertEqual(s, 1)
        self.assertEqual(t, 2)
        
    def test__refid_for_missing(self):
        inst = self._makeOne()
        self.assertRaises(ValueError, inst._refid_for, 1)
        
    def test__refid_for_success_oid(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        oid = inst._refid_for(1)
        self.assertEqual(oid, 1)

    def test__refid_for_success_object(self):
        inst = self._makeOne()
        obj = testing.DummyResource()
        obj.__objectid__ = 1
        inst.objectid_to_path[1] = (u'',)
        oid = inst._refid_for(obj)
        self.assertEqual(oid, 1)

    def test_connect(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        inst.objectid_to_path[2] = (u'', u'a')
        inst.referencemap = DummyReferenceMap()
        inst.connect(1, 2, 'ref')
        self.assertEqual(inst.referencemap['ref'], (1, 2))

    def test_disconnect(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        inst.objectid_to_path[2] = (u'', u'a')
        inst.referencemap = DummyReferenceMap()
        inst.referencemap['ref'] = True
        inst.disconnect(1, 2, 'ref')
        self.assertTrue('ref' not in inst.referencemap)

    def test_disconnect_with_objects(self):
        one = testing.DummyResource(__objectid__=1)
        two = testing.DummyResource(__objectid__=2)
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        inst.objectid_to_path[2] = (u'', u'a')
        inst.referencemap = DummyReferenceMap()
        inst.referencemap['ref'] = True
        inst.disconnect(one, two, 'ref')
        self.assertTrue('ref' not in inst.referencemap)
        
    def test_sourceids(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        inst.referencemap = DummyReferenceMap(sourceids=[2])
        self.assertEqual(list(inst.sourceids(1, 'ref')), [2])
        
    def test_targetids(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        inst.referencemap = DummyReferenceMap(targetids=[2])
        self.assertEqual(list(inst.targetids(1, 'ref')), [2])

    def test_sources(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        inst.objectid_to_path[2] = (u'', u'a')
        inst.objectid_to_path[3] = (u'', u'b')
        inst.referencemap = DummyReferenceMap(sourceids=[2, 3])
        obj = object()
        inst._find_resource = lambda *arg: obj
        self.assertEqual(list(inst.sources(1, 'ref')), [obj, obj])
        
    def test_targets(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        inst.objectid_to_path[2] = (u'', u'a')
        inst.objectid_to_path[3] = (u'', u'b')
        inst.referencemap = DummyReferenceMap(targetids=[2, 3])
        obj = object()
        inst._find_resource = lambda *arg: obj
        self.assertEqual(list(inst.targets(1, 'ref')), [obj, obj])
        
class TestReferenceSet(unittest.TestCase):
    def _makeOne(self):
        from . import ReferenceSet
        return ReferenceSet()

    def test_connect_empty(self):
        refset = self._makeOne()
        refset.connect(1, 2)
        self.assertEqual(list(refset.src2target[1]), [2])
        self.assertEqual(list(refset.target2src[2]), [1])
        
    def test_connect_nonempty_overlap(self):
        refset = self._makeOne()
        refset.src2target[1] = DummyTreeSet([2])
        refset.target2src[2] = DummyTreeSet([1])
        refset.connect(1, 2)
        self.assertEqual(list(refset.src2target[1]), [2])
        self.assertEqual(list(refset.target2src[2]), [1])

    def test_connect_nonempty_nonoverlap(self):
        refset = self._makeOne()
        refset.src2target[1] = DummyTreeSet([3])
        refset.target2src[2] = DummyTreeSet([4])
        refset.connect(1, 2)
        self.assertEqual(sorted(list(refset.src2target[1])), [2, 3])
        self.assertEqual(sorted(list(refset.target2src[2])), [1, 4])

    def test_disconnect_empty(self):
        refset = self._makeOne()
        refset.disconnect(1, 2)
        self.assertEqual(list(refset.src2target.keys()), [])
        self.assertEqual(list(refset.target2src.keys()), [])
        
    def test_disconnect_nonempty(self):
        refset = self._makeOne()
        refset.src2target[1] = DummyTreeSet([2, 3])
        refset.target2src[2] = DummyTreeSet([1, 4])
        refset.disconnect(1, 2)
        self.assertEqual(list(refset.src2target[1]), [3])
        self.assertEqual(list(refset.target2src[2]), [4])

    def test_disconnect_keyerrors(self):
        refset = self._makeOne()
        refset.src2target[1] = DummyTreeSet()
        refset.target2src[2] = DummyTreeSet()
        refset.disconnect(1, 2)
        self.assertEqual(list(refset.src2target[1]), [])
        self.assertEqual(list(refset.target2src[2]), [])

    def test_targetids(self):
        refset = self._makeOne()
        dummyset = DummyTreeSet([1])
        refset.src2target[1] = dummyset
        self.assertEqual(refset.targetids(1), dummyset)
        
    def test_sourceids(self):
        refset = self._makeOne()
        dummyset = DummyTreeSet([1])
        refset.target2src[1] = dummyset
        self.assertEqual(refset.sourceids(1), dummyset)

    def test_remove_empty(self):
        refset = self._makeOne()
        self.assertEqual(list(refset.remove([1,2])), [])

    def test_remove_notempty(self):
        # emulate the result of:
        # connect(1, 2)
        # connect(3, 4)
        # connect(2, 4)
        # connect(2, 1)
        # connect(3, 5)
        src2target = {1:DummyTreeSet([2]), 3:DummyTreeSet([4, 5]), 
                      2:DummyTreeSet([4, 1])}
        target2src = {2:DummyTreeSet([1]), 4:DummyTreeSet([3, 2]),
                      1:DummyTreeSet([2]), 5:DummyTreeSet([3])}
        refset = self._makeOne()
        refset.src2target = src2target
        refset.target2src = target2src
        oids = [1,4, 10]
        result = refset.remove(oids)
        self.assertEqual(list(result), [1,4]) # 10 unmentioned
        self.assertEqual(
            src2target,
            {3:DummyTreeSet([5])}
            )
        self.assertEqual(
            target2src,
            {5:DummyTreeSet([3])}
            )

class TestReferenceMap(unittest.TestCase):
    def _makeOne(self, map=None):
        from . import ReferenceMap
        return ReferenceMap(map)

    def test_ctor(self):
        refs = self._makeOne()
        self.assertEqual(refs.refmap.__class__.__name__, 'OOBTree')

    def test_connect(self):
        refset = DummyReferenceSet()
        map = {'reftype':refset}
        refs = self._makeOne(map)
        refs.connect('a', 'b', 'reftype')
        self.assertEqual(refset.connected, [('a', 'b')])
        
    def test_disconnect(self):
        refset = DummyReferenceSet()
        map = {'reftype':refset}
        refs = self._makeOne(map)
        refs.disconnect('a', 'b', 'reftype')
        self.assertEqual(refset.disconnected, [('a', 'b')])

    def test_targetids_no_refset(self):
        refs = self._makeOne()
        self.assertEqual(list(refs.targetids('a', 'reftype')), [])
        
    def test_targetids_with_refset(self):
        refset = DummyReferenceSet(['123'])
        map = {'reftype':refset}
        refs = self._makeOne(map)
        self.assertEqual(list(refs.targetids('a', 'reftype')), ['123'])

    def test_sourceids_no_refset(self):
        refs = self._makeOne()
        self.assertEqual(list(refs.sourceids('a', 'reftype')), [])
        
    def test_sourceids_with_refset(self):
        refset = DummyReferenceSet(['123'])
        map = {'reftype':refset}
        refs = self._makeOne(map)
        self.assertEqual(list(refs.sourceids('a', 'reftype')), ['123'])

    def test_remove(self):
        L = []
        refset1 = DummyReferenceSet()
        refset2 = DummyReferenceSet()
        refset1.remove = lambda oids: L.append(oids)
        refset2.remove = lambda oids: L.append(oids)
        map = {'reftype':refset1, 'reftype2':refset2}
        refs = self._makeOne(map)
        refs.remove([1,2])
        self.assertEqual(L, [[1,2], [1,2]])

class Test_object_will_be_added(unittest.TestCase):
    def _callFUT(self, event):
        from . import object_will_be_added
        return object_will_be_added(event)

    def test_no_objectmap(self):
        model = testing.DummyResource()
        event = DummyEvent(model, None)
        self._callFUT(event) # doesnt blow up

    def test_added_object_has_children(self):
        from ..interfaces import IFolder
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap)
        one = testing.DummyModel(__provides__=IFolder)
        two = testing.DummyModel(__provides__=IFolder)
        one['two'] = two
        event = DummyEvent(one, site)
        event.name = 'one'
        self._callFUT(event)
        self.assertEqual(
            objectmap.added,
            [(two, ('', 'one', 'two')), (one, ('', 'one'))]
            )

    def test_added_object_has_children_object_has_no_name(self):
        from ..interfaces import IFolder
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap)
        one = testing.DummyModel(__provides__=IFolder)
        two = testing.DummyModel(__provides__=IFolder)
        one['two'] = two
        event = DummyEvent(one, site)
        event.name = 'one'
        del one.__name__
        self._callFUT(event)
        self.assertEqual(
            objectmap.added,
            [(two, ('', 'one', 'two')), (one, ('', 'one'))]
            )
        
    def test_added_object_has_children_not_adding_to_root(self):
        from ..interfaces import IFolder
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap)
        one = testing.DummyModel(__provides__=IFolder)
        two = testing.DummyModel(__provides__=IFolder)
        inter = testing.DummyModel()
        site['inter'] = inter
        one['two'] = two
        event = DummyEvent(one, inter)
        event.name = 'one'
        self._callFUT(event)
        self.assertEqual(
            objectmap.added,
            [(two, ('', 'inter', 'one', 'two')), (one, ('', 'inter', 'one'))]
            )
        
    def test_object_has_a_parent(self):
        from ..interfaces import IFolder
        from pyramid.traversal import resource_path_tuple
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap)
        bogusroot = testing.DummyModel(__provides__=IFolder)
        bogusparent2 = testing.DummyModel(__provides__=IFolder)
        one = testing.DummyModel(__provides__=IFolder)
        two = testing.DummyModel(__provides__=IFolder)
        bogusroot['bogusparent2'] = bogusparent2
        bogusparent2['one'] = one
        one['two'] = two
        self.assertEqual(resource_path_tuple(one), 
                         ('', 'bogusparent2', 'one'))
        event = DummyEvent(one, site)
        self.assertRaises(ValueError, self._callFUT, event)

class Test_object_removed(unittest.TestCase):
    def _callFUT(self, event):
        from . import object_removed
        return object_removed(event)

    def test_no_objectmap(self):
        model = testing.DummyResource()
        event = DummyEvent(model, None)
        self._callFUT(event) # doesnt blow up

    def test_it(self):
        model = testing.DummyResource()
        model.__objectid__ = 1
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap)
        event = DummyEvent(model, site)
        self._callFUT(event)
        self.assertEqual(objectmap.removed, [1])
        self.assertTrue(objectmap.references_removed)

    def test_moving(self):
        model = testing.DummyResource()
        model.__objectid__ = 1
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap)
        event = DummyEvent(model, site, moving=True)
        self._callFUT(event)
        self.assertEqual(objectmap.removed, [1])
        self.assertFalse(objectmap.references_removed)

class Test_referenceid_source_property(unittest.TestCase):
    def setUp(self):
        from substanced.interfaces import IFolder
        @implementer(IFolder)
        class DummyFolder(dict):
            pass
        self.DummyFolder = DummyFolder

    def _makeInst(self, reftype=None):
        if reftype is None:
            reftype = Dummy
        from . import referenceid_source_property
        class Inner(self.DummyFolder):
            prop = referenceid_source_property(reftype)
        inst = Inner()
        return inst

    def test_get_no_targetids(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=())
        self.assertEqual(inst.prop, None)

    def test_get_one_targetid(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(1,))
        self.assertEqual(inst.prop, 1)

    def test_get_gt_one_targetid(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(1,2))
        self.assertRaises(AssertionError, getattr, inst, 'prop')

    def test_del_no_target_id(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=())
        del inst.prop
        self.assertEqual(inst.prop, None)

    def test_del_one_targetid(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(1,))
        del inst.prop
        self.assertEqual(svcs['objectmap'].disconnected, [(inst, 1, Dummy)])

    def test_set_None(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=())
        inst.prop = None
        self.assertEqual(svcs['objectmap'].connected, [])

    def test_set_not_None(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=())
        inst.prop = 2
        self.assertEqual(svcs['objectmap'].connected, [(inst, 2, Dummy)])

class Test_referenceid_target_property(unittest.TestCase):
    def setUp(self):
        from substanced.interfaces import IFolder
        @implementer(IFolder)
        class DummyFolder(dict):
            pass
        self.DummyFolder = DummyFolder

    def _makeInst(self, reftype=None):
        if reftype is None:
            reftype = Dummy
        from . import referenceid_target_property
        class Inner(self.DummyFolder):
            prop = referenceid_target_property(reftype)
        inst = Inner()
        return inst

    def test_get_no_sourceids(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=())
        self.assertEqual(inst.prop, None)

    def test_get_one_sourceid(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(1,))
        self.assertEqual(inst.prop, 1)

    def test_get_gt_one_sourceid(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(1,2))
        self.assertRaises(AssertionError, getattr, inst, 'prop')

    def test_del_no_source_id(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=())
        del inst.prop
        self.assertEqual(inst.prop, None)

    def test_del_one_sourceid(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(1,))
        del inst.prop
        self.assertEqual(svcs['objectmap'].disconnected, [(1, inst, Dummy)])

    def test_set_None(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=())
        inst.prop = None
        self.assertEqual(svcs['objectmap'].connected, [])

    def test_set_not_None(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=())
        inst.prop = 2
        self.assertEqual(svcs['objectmap'].connected, [(2, inst, Dummy)])

class Test_reference_source_property(unittest.TestCase):
    def setUp(self):
        from substanced.interfaces import IFolder
        @implementer(IFolder)
        class DummyFolder(dict):
            pass
        self.DummyFolder = DummyFolder

    def _makeInst(self, reftype=None):
        if reftype is None:
            reftype = Dummy
        from . import reference_source_property
        class Inner(self.DummyFolder):
            prop = reference_source_property(reftype)
        inst = Inner()
        inst.__objectid__ = 1
        return inst

    def test_get_no_targetids(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=())
        self.assertEqual(inst.prop, None)

    def test_get_one_targetid(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        ob = object()
        svcs['objectmap'] = DummyObjectMap(targetids=(1,), result=ob)
        self.assertEqual(inst.prop, ob)

    def test_get_gt_one_targetid(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(1,2))
        self.assertRaises(AssertionError, getattr, inst, 'prop')

    def test_del_no_target_id(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=())
        del inst.prop
        self.assertEqual(inst.prop, None)

    def test_del_one_targetid(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(1,))
        del inst.prop
        self.assertEqual(svcs['objectmap'].disconnected, [(inst, 1, Dummy)])

    def test_set_None(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=())
        inst.prop = None
        self.assertEqual(svcs['objectmap'].connected, [])

    def test_set_not_None(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=())
        inst.prop = 2
        self.assertEqual(svcs['objectmap'].connected, [(inst, 2, Dummy)])

class Test_reference_target_property(unittest.TestCase):
    def setUp(self):
        from substanced.interfaces import IFolder
        @implementer(IFolder)
        class DummyFolder(dict):
            pass
        self.DummyFolder = DummyFolder

    def _makeInst(self, reftype=None):
        if reftype is None:
            reftype = Dummy
        from . import reference_target_property
        class Inner(self.DummyFolder):
            prop = reference_target_property(reftype)
        inst = Inner()
        inst.__objectid__ = 1
        return inst

    def test_get_no_sourceids(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=())
        self.assertEqual(inst.prop, None)

    def test_get_one_sourceid(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        ob = object()
        svcs['objectmap'] = DummyObjectMap(sourceids=(1,), result=ob)
        self.assertEqual(inst.prop, ob)

    def test_get_gt_one_sourceid(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(1,2))
        self.assertRaises(AssertionError, getattr, inst, 'prop')

    def test_del_no_source_id(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=())
        del inst.prop
        self.assertEqual(inst.prop, None)

    def test_del_one_sourceid(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(1,))
        del inst.prop
        self.assertEqual(svcs['objectmap'].disconnected, [(1, inst, Dummy)])

    def test_set_None(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=())
        inst.prop = None
        self.assertEqual(svcs['objectmap'].connected, [])

    def test_set_not_None(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=())
        inst.prop = 2
        self.assertEqual(svcs['objectmap'].connected, [(2, inst, Dummy)])

class Test_multireferenceid_source_property(unittest.TestCase):
    def setUp(self):
        from substanced.interfaces import IFolder
        @implementer(IFolder)
        class DummyFolder(dict):
            pass
        self.DummyFolder = DummyFolder

    def _makeInst(self, reftype=None, ignore_missing=False):
        if reftype is None:
            reftype = Dummy
        from . import multireference_sourceid_property
        class Inner(self.DummyFolder):
            prop = multireference_sourceid_property(
                reftype,
                ignore_missing=ignore_missing,
                )
        inst = Inner()
        inst.__objectid__ = -1
        return inst

    def test_get_zero(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=())
        self.assertEqual(list(inst.prop), [])

    def test_get_one(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(1,))
        self.assertEqual(list(inst.prop), [1])

    def test_get_two(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(1,2))
        self.assertEqual(list(inst.prop), [1,2])

    def test_del_zero(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=())
        del inst.prop
        self.assertEqual(list(inst.prop), [])

    def test_del_one(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(1,))
        del inst.prop
        self.assertEqual(svcs['objectmap'].disconnected, [(-1, 1, Dummy)])

    def test_del_two(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(1,2))
        del inst.prop
        self.assertEqual(svcs['objectmap'].disconnected,
                         [(-1, 1, Dummy), (-1, 2, Dummy)])

    def test_set_None(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=())
        self.assertRaises(ValueError, inst.__setattr__, 'prop', None)

    def test_set_zero(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(1,))
        inst.prop = []
        self.assertEqual(svcs['objectmap'].disconnected, [(-1, 1, Dummy)])
        self.assertEqual(svcs['objectmap'].connected, [])

    def test_set_one(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(1,))
        inst.prop = [2]
        self.assertEqual(svcs['objectmap'].disconnected, [(-1, 1, Dummy)])
        self.assertEqual(svcs['objectmap'].connected, [(-1, 2, Dummy)])

    def test_set_two(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(1,))
        inst.prop = [2, 3]
        self.assertEqual(svcs['objectmap'].disconnected, [(-1, 1, Dummy)])
        self.assertEqual(svcs['objectmap'].connected,
                         [(-1, 2, Dummy), (-1, 3, Dummy)])

    def test_clear(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(1,))
        inst.prop.clear()
        self.assertEqual(svcs['objectmap'].disconnected, [(-1, 1, Dummy)])

    def test_connect(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=())
        inst.prop.connect([2,3])
        self.assertEqual(svcs['objectmap'].connected,
                         [(-1, 2, Dummy), (-1, 3, Dummy)])
        
    def test_connect_missing(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(),
                                           toraise=ValueError('a'))
        self.assertRaises(ValueError, inst.prop.connect, [2,3])

    def test_connect_with_ignore_missing(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(),
                                           toraise=ValueError('a'))
        inst.prop.connect([2,3], ignore_missing=True)
        self.assertEqual(svcs['objectmap'].connected, [])

    def test_disconnect(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=())
        inst.prop.disconnect([2,3])
        self.assertEqual(svcs['objectmap'].disconnected,
                         [(-1, 2, Dummy), (-1, 3, Dummy)])
        
    def test_disconnect_missing(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(),
                                           toraise=ValueError('a'))
        self.assertRaises(ValueError, inst.prop.disconnect, [2,3])

    def test_disconnect_with_ignore_missing(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(),
                                           toraise=ValueError('a'))
        inst.prop.disconnect([2,3], ignore_missing=True)
        self.assertEqual(svcs['objectmap'].disconnected, [])

    def test_ignore_missing_implicit(self):
        inst = self._makeInst(ignore_missing=True)
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(),
                                           toraise=ValueError('a'))
        inst.prop.disconnect([2,3])
        self.assertEqual(svcs['objectmap'].disconnected, [])

class Test_multireference_source_property(unittest.TestCase):
    def setUp(self):
        from substanced.interfaces import IFolder
        @implementer(IFolder)
        class DummyFolder(dict):
            pass
        self.DummyFolder = DummyFolder

    def _makeInst(self, reftype=None, ignore_missing=False):
        if reftype is None:
            reftype = Dummy
        from . import multireference_source_property
        class Inner(self.DummyFolder):
            prop = multireference_source_property(
                reftype,
                ignore_missing=ignore_missing
                )
        inst = Inner()
        inst.__objectid__ = -1
        return inst

    def test_get_zero(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=())
        self.assertEqual(list(inst.prop), [])

    def test_get_one(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(1,), result=object)
        self.assertEqual(list(inst.prop), [object])

    def test_get_two(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(1,2), result=object)
        self.assertEqual(list(inst.prop), [object, object])

    def test_del_zero(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=())
        del inst.prop
        self.assertEqual(list(inst.prop), [])

    def test_del_one(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(1,))
        del inst.prop
        self.assertEqual(svcs['objectmap'].disconnected, [(-1, 1, Dummy)])

    def test_del_two(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(1,2))
        del inst.prop
        self.assertEqual(svcs['objectmap'].disconnected,
                         [(-1, 1, Dummy), (-1, 2, Dummy)])

    def test_set_None(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=())
        self.assertRaises(ValueError, inst.__setattr__, 'prop', None)

    def test_set_zero(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(1,))
        inst.prop = []
        self.assertEqual(svcs['objectmap'].disconnected, [(-1, 1, Dummy)])
        self.assertEqual(svcs['objectmap'].connected, [])

    def test_set_one(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(1,))
        inst.prop = [2]
        self.assertEqual(svcs['objectmap'].disconnected, [(-1, 1, Dummy)])
        self.assertEqual(svcs['objectmap'].connected, [(-1, 2, Dummy)])

    def test_set_two(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(1,))
        inst.prop = [2, 3]
        self.assertEqual(svcs['objectmap'].disconnected, [(-1, 1, Dummy)])
        self.assertEqual(svcs['objectmap'].connected,
                         [(-1, 2, Dummy), (-1, 3, Dummy)])

    def test_clear(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(1,))
        inst.prop.clear()
        self.assertEqual(svcs['objectmap'].disconnected, [(-1, 1, Dummy)])

    def test_connect(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=())
        inst.prop.connect([2,3])
        self.assertEqual(svcs['objectmap'].connected,
                         [(-1, 2, Dummy), (-1, 3, Dummy)])
        
    def test_connect_missing(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(),
                                           toraise=ValueError('a'))
        self.assertRaises(ValueError, inst.prop.connect, [2,3])

    def test_connect_with_ignore_missing(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(),
                                           toraise=ValueError('a'))
        inst.prop.connect([2,3], ignore_missing=True)
        self.assertEqual(svcs['objectmap'].connected, [])

    def test_disconnect(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=())
        inst.prop.disconnect([2,3])
        self.assertEqual(svcs['objectmap'].disconnected,
                         [(-1, 2, Dummy), (-1, 3, Dummy)])
        
    def test_disconnect_missing(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(),
                                           toraise=ValueError('a'))
        self.assertRaises(ValueError, inst.prop.disconnect, [2,3])

    def test_disconnect_with_ignore_missing(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(),
                                           toraise=ValueError('a'))
        inst.prop.disconnect([2,3], ignore_missing=True)
        self.assertEqual(svcs['objectmap'].disconnected, [])

    def test_ignore_missing_implicit(self):
        inst = self._makeInst(ignore_missing=True)
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(targetids=(),
                                           toraise=ValueError('a'))
        inst.prop.disconnect([2,3])
        self.assertEqual(svcs['objectmap'].disconnected, [])

class Test_multireference_targetid_property(unittest.TestCase):
    def setUp(self):
        from substanced.interfaces import IFolder
        @implementer(IFolder)
        class DummyFolder(dict):
            pass
        self.DummyFolder = DummyFolder

    def _makeInst(self, reftype=None, ignore_missing=False):
        if reftype is None:
            reftype = Dummy
        from . import multireference_targetid_property
        class Inner(self.DummyFolder):
            prop = multireference_targetid_property(
                reftype,
                ignore_missing=ignore_missing
                )
        inst = Inner()
        inst.__objectid__ = -1
        return inst

    def test_get_zero(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=())
        self.assertEqual(list(inst.prop), [])

    def test_get_one(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(1,))
        self.assertEqual(list(inst.prop), [1])

    def test_get_two(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(1,2))
        self.assertEqual(list(inst.prop), [1,2])

    def test_del_zero(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=())
        del inst.prop
        self.assertEqual(list(inst.prop), [])

    def test_del_one(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(1,))
        del inst.prop
        self.assertEqual(svcs['objectmap'].disconnected, [(1, -1, Dummy)])

    def test_del_two(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(1,2))
        del inst.prop
        self.assertEqual(svcs['objectmap'].disconnected,
                         [(1, -1, Dummy), (2, -1, Dummy)])

    def test_set_None(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=())
        self.assertRaises(ValueError, inst.__setattr__, 'prop', None)

    def test_set_zero(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(1,))
        inst.prop = []
        self.assertEqual(svcs['objectmap'].disconnected, [(1, -1, Dummy)])
        self.assertEqual(svcs['objectmap'].connected, [])

    def test_set_one(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(1,))
        inst.prop = [2]
        self.assertEqual(svcs['objectmap'].disconnected, [(1, -1, Dummy)])
        self.assertEqual(svcs['objectmap'].connected, [(2, -1, Dummy)])

    def test_set_two(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(1,))
        inst.prop = [2, 3]
        self.assertEqual(svcs['objectmap'].disconnected, [(1, -1, Dummy)])
        self.assertEqual(svcs['objectmap'].connected,
                         [(2, -1, Dummy), (3, -1, Dummy)])

    def test_clear(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(1,))
        inst.prop.clear()
        self.assertEqual(svcs['objectmap'].disconnected, [(1, -1, Dummy)])

    def test_connect(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=())
        inst.prop.connect([2,3])
        self.assertEqual(svcs['objectmap'].connected,
                         [(2, -1, Dummy), (3, -1, Dummy)])
        
    def test_connect_missing(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(),
                                           toraise=ValueError('a'))
        self.assertRaises(ValueError, inst.prop.connect, [2,3])

    def test_connect_with_ignore_missing(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(),
                                           toraise=ValueError('a'))
        inst.prop.connect([2,3], ignore_missing=True)
        self.assertEqual(svcs['objectmap'].connected, [])

    def test_disconnect(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=())
        inst.prop.disconnect([2,3])
        self.assertEqual(svcs['objectmap'].disconnected,
                         [(2, -1, Dummy), (3, -1, Dummy)])
        
    def test_disconnect_missing(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(),
                                           toraise=ValueError('a'))
        self.assertRaises(ValueError, inst.prop.disconnect, [2,3])

    def test_disconnect_with_ignore_missing(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(),
                                           toraise=ValueError('a'))
        inst.prop.disconnect([2,3], ignore_missing=True)
        self.assertEqual(svcs['objectmap'].disconnected, [])

    def test_ignore_missing_implicit(self):
        inst = self._makeInst(ignore_missing=True)
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(),
                                           toraise=ValueError('a'))
        inst.prop.disconnect([2,3])
        self.assertEqual(svcs['objectmap'].disconnected, [])

class Test_multireference_target_property(unittest.TestCase):
    def setUp(self):
        from substanced.interfaces import IFolder
        @implementer(IFolder)
        class DummyFolder(dict):
            pass
        self.DummyFolder = DummyFolder

    def _makeInst(self, reftype=None, ignore_missing=False):
        if reftype is None:
            reftype = Dummy
        from . import multireference_target_property
        class Inner(self.DummyFolder):
            prop = multireference_target_property(
                reftype,
                ignore_missing=ignore_missing
                )
        inst = Inner()
        inst.__objectid__ = -1
        return inst

    def test_get_zero(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=())
        self.assertEqual(list(inst.prop), [])

    def test_get_one(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(1,), result=object)
        self.assertEqual(list(inst.prop), [object])

    def test_get_two(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(1,2), result=object)
        self.assertEqual(list(inst.prop), [object, object])

    def test_del_zero(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=())
        del inst.prop
        self.assertEqual(list(inst.prop), [])

    def test_del_one(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(1,))
        del inst.prop
        self.assertEqual(svcs['objectmap'].disconnected, [(1, -1, Dummy)])

    def test_del_two(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(1,2))
        del inst.prop
        self.assertEqual(svcs['objectmap'].disconnected,
                         [(1, -1, Dummy), (2, -1, Dummy)])

    def test_set_None(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=())
        self.assertRaises(ValueError, inst.__setattr__, 'prop', None)

    def test_set_zero(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(1,))
        inst.prop = []
        self.assertEqual(svcs['objectmap'].disconnected, [(1, -1, Dummy)])
        self.assertEqual(svcs['objectmap'].connected, [])

    def test_set_one(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(1,))
        inst.prop = [2]
        self.assertEqual(svcs['objectmap'].disconnected, [(1, -1, Dummy)])
        self.assertEqual(svcs['objectmap'].connected, [(2, -1, Dummy)])

    def test_set_two(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(1,))
        inst.prop = [2, 3]
        self.assertEqual(svcs['objectmap'].disconnected, [(1, -1, Dummy)])
        self.assertEqual(svcs['objectmap'].connected,
                         [(2, -1, Dummy), (3, -1, Dummy)])

    def test_clear(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(1,))
        inst.prop.clear()
        self.assertEqual(svcs['objectmap'].disconnected, [(1, -1, Dummy)])

    def test_connect(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=())
        inst.prop.connect([2,3])
        self.assertEqual(svcs['objectmap'].connected,
                         [(2, -1, Dummy), (3, -1, Dummy)])
        
    def test_connect_missing(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(),
                                           toraise=ValueError('a'))
        self.assertRaises(ValueError, inst.prop.connect, [2,3])

    def test_connect_with_ignore_missing(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(),
                                           toraise=ValueError('a'))
        inst.prop.connect([2,3], ignore_missing=True)
        self.assertEqual(svcs['objectmap'].connected, [])

    def test_disconnect(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=())
        inst.prop.disconnect([2,3])
        self.assertEqual(svcs['objectmap'].disconnected,
                         [(2, -1, Dummy), (3, -1, Dummy)])
        
    def test_disconnect_missing(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(),
                                           toraise=ValueError('a'))
        self.assertRaises(ValueError, inst.prop.disconnect, [2,3])

    def test_disconnect_with_ignore_missing(self):
        inst = self._makeInst()
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(),
                                           toraise=ValueError('a'))
        inst.prop.disconnect([2,3], ignore_missing=True)
        self.assertEqual(svcs['objectmap'].disconnected, [])

    def test_ignore_missing_implicit(self):
        inst = self._makeInst(ignore_missing=True)
        svcs = inst['__services__'] = self.DummyFolder()
        svcs['objectmap'] = DummyObjectMap(sourceids=(),
                                           toraise=ValueError('a'))
        inst.prop.disconnect([2,3])
        self.assertEqual(svcs['objectmap'].disconnected, [])

class TestMultireference(unittest.TestCase):
    def _makeOne(
        self,
        context,
        oids,
        objectmap,
        ignore_missing=False,
        resolve=False,
        orientation='source'
        ):
        from . import Multireference
        return Multireference(
            context,
            oids,
            objectmap,
            'reftype',
            ignore_missing=ignore_missing,
            resolve=resolve,
            orientation=orientation
            )

    def _makeContext(self):
        resource = testing.DummyResource()
        resource.__objectid__ = -1
        return resource

    def test___nonzero__True(self):
        inst = self._makeOne(None, [1], None)
        self.assertTrue(inst.__nonzero__())
        
    def test___nonzero__False(self):
        inst = self._makeOne(None, [], None)
        self.assertFalse(inst.__nonzero__())

    def test___getitem__(self):
        inst = self._makeOne(None, [1], None)
        self.assertEqual(inst[0], 1)

    def test___getitem___with_resolve(self):
        objectmap = DummyObjectMap(result=object)
        inst = self._makeOne(None, [1], objectmap, resolve=True)
        self.assertEqual(inst[0], object)
        
    def test___contains__True(self):
        inst = self._makeOne(None, [1], None)
        self.assertTrue(inst.__contains__(1))
        
    def test___contains__False(self):
        inst = self._makeOne(None, [], None)
        self.assertFalse(inst.__contains__(1))
            
    def test___contains___withresolve_True(self):
        objectmap = DummyObjectMap(result=object)
        inst = self._makeOne(None, [1], objectmap, resolve=True)
        self.assertTrue(inst.__contains__(object))
        
    def test___contains___withresolve_False_empty(self):
        objectmap = DummyObjectMap(result=object)
        inst = self._makeOne(None, [], objectmap, resolve=True)
        self.assertFalse(inst.__contains__(object))

    def test___contains___withresolve_False_nonempty(self):
        objectmap = DummyObjectMap(result=object)
        inst = self._makeOne(None, [1], objectmap, resolve=True)
        self.assertFalse(inst.__contains__(None))

    def test___iter__(self):
        inst = self._makeOne(None, [1], None)
        self.assertEqual(list(inst.__iter__()), [1])

    def test___iter__withresolve(self):
        objectmap = DummyObjectMap(result=object)
        inst = self._makeOne(None, [1], objectmap, resolve=True)
        self.assertEqual(list(inst.__iter__()), [object])

    def test___len__(self):
        inst = self._makeOne(None, [1], None)
        self.assertEqual(len(inst), 1)

    def test_connect_zero(self):
        objectmap = DummyObjectMap()
        context = self._makeContext()
        inst = self._makeOne(context, [1], objectmap)
        inst.connect([])
        self.assertEqual(objectmap.connected, [])
        
    def test_connect_one(self):
        objectmap = DummyObjectMap()
        context = self._makeContext()
        inst = self._makeOne(context, [1], objectmap)
        inst.connect([1])
        self.assertEqual(objectmap.connected, [(-1, 1, 'reftype')])

    def test_connect_two(self):
        objectmap = DummyObjectMap()
        context = self._makeContext()
        inst = self._makeOne(context, [1, 2], objectmap)
        inst.connect([1, 2])
        self.assertEqual(
            objectmap.connected,
            [(-1, 1, 'reftype'), (-1, 2, 'reftype')]
            )

    def test_connect_ignore_missing_explicit(self):
        objectmap = DummyObjectMap(toraise=ValueError('a'))
        context = self._makeContext()
        inst = self._makeOne(context, [1, 2], objectmap)
        inst.connect([1, 2], ignore_missing=True)
        self.assertEqual(objectmap.connected, [])

    def test_connect_ignore_missing_implicit(self):
        objectmap = DummyObjectMap(toraise=ValueError('a'))
        context = self._makeContext()
        inst = self._makeOne(context, [1, 2], objectmap, ignore_missing=True)
        inst.connect([1, 2])
        self.assertEqual(objectmap.connected, [])

    def test_connect_nonsource(self):
        objectmap = DummyObjectMap()
        context = self._makeContext()
        inst = self._makeOne(context, [1, 2], objectmap, orientation='target')
        inst.connect([1, 2])
        self.assertEqual(
            objectmap.connected,
            [(1, -1, 'reftype'), (2, -1, 'reftype')]
            )

    def test_disconnect_zero(self):
        objectmap = DummyObjectMap()
        context = self._makeContext()
        inst = self._makeOne(context, [1], objectmap)
        inst.disconnect([])
        self.assertEqual(objectmap.disconnected, [])
        
    def test_disconnect_one(self):
        objectmap = DummyObjectMap()
        context = self._makeContext()
        inst = self._makeOne(context, [1], objectmap)
        inst.disconnect([1])
        self.assertEqual(objectmap.disconnected, [(-1, 1, 'reftype')])

    def test_disconnect_two(self):
        objectmap = DummyObjectMap()
        context = self._makeContext()
        inst = self._makeOne(context, [1, 2], objectmap)
        inst.disconnect([1, 2])
        self.assertEqual(
            objectmap.disconnected,
            [(-1, 1, 'reftype'), (-1, 2, 'reftype')]
            )

    def test_disconnect_ignore_missing_explicit(self):
        objectmap = DummyObjectMap(toraise=ValueError('a'))
        context = self._makeContext()
        inst = self._makeOne(context, [1, 2], objectmap)
        inst.disconnect([1, 2], ignore_missing=True)
        self.assertEqual(objectmap.disconnected, [])

    def test_disconnect_ignore_missing_implicit(self):
        objectmap = DummyObjectMap(toraise=ValueError('a'))
        context = self._makeContext()
        inst = self._makeOne(context, [1, 2], objectmap, ignore_missing=True)
        inst.disconnect([1, 2])
        self.assertEqual(objectmap.disconnected, [])

    def test_disconnect_nonsource(self):
        objectmap = DummyObjectMap()
        context = self._makeContext()
        inst = self._makeOne(context, [1, 2], objectmap, orientation='target')
        inst.disconnect([1, 2])
        self.assertEqual(
            objectmap.disconnected,
            [(1, -1, 'reftype'), (2, -1, 'reftype')]
            )

    def test_clear(self):
        objectmap = DummyObjectMap()
        context = self._makeContext()
        inst = self._makeOne(context, [1, 2], objectmap)
        inst.clear()
        self.assertEqual(
            objectmap.disconnected,
            [(-1, 1, 'reftype'), (-1, 2, 'reftype')]
            )

class Dummy(object):
    pass

def resource(path):
    path_tuple = split(path)
    parent = None
    for element in path_tuple:
        obj = testing.DummyResource()
        obj.__parent__ = parent
        obj.__name__ = element
        parent = obj
    obj.path_tuple = path_tuple
    return obj
                
        
def split(s):
    return (u'',) + tuple(filter(None, s.split(u'/')))

class DummyObjectMap(object):
    def __init__(self, targetids=(), sourceids=(), result=None, toraise=None):
        self.added = []
        self.removed = []
        self.connected = []
        self.disconnected = []
        self._targetids = targetids
        self._sourceids = sourceids
        self.result = result
        self.toraise = toraise

    def add(self, obj, path, replace_oid=False):
        self.added.append((obj, path))
        objectid = getattr(obj, '__objectid__', None)
        if objectid is None:
            objectid = 1
            obj.__objectid__ = objectid
        return objectid

    def remove(self, objectid, references=True):
        self.references_removed = references
        self.removed.append(objectid)
        return [objectid]

    def object_for(self, objectid):
        return self.result

    def targetids(self, context, reftype):
        return self._targetids

    def sourceids(self, context, reftype):
        return self._sourceids

    def disconnect(self, source, target, reftype):
        if self.toraise:
            raise self.toraise
        self.disconnected.append((source, target, reftype))

    def connect(self, source, target, reftype):
        if self.toraise:
            raise self.toraise
        self.connected.append((source, target, reftype))


class DummyEvent(object):
    def __init__(self, object, parent, moving=False, duplicating=False):
        self.object = object
        self.parent = parent
        self.moving = moving
        self.duplicating = duplicating

class DummyTreeSet(set):
    def insert(self, val):
        self.add(val)

class DummyReferenceSet(object):
    def __init__(self, result=True):
        self.result = result
        self.connected = []
        self.disconnected = []

    def connect(self, src, target):
        self.connected.append((src, target))

    def disconnect(self, src, target):
        self.disconnected.append((src, target))

    def targetids(self, src):
        return self.result

    def sourceids(self, src):
        return self.result

class DummyReferenceMap(dict):
    def __init__(self, sourceids=(), targetids=()):
        self._sourceids = sourceids
        self._targetids = targetids
        
    def connect(self, src, target, reftype):
        self[reftype] = (src, target)

    def disconnect(self, src, target, reftype):
        del self[reftype]

    def sourceids(self, oid, reftype):
        return self._sourceids

    def targetids(self, oid, reftype):
        return self._targetids

def _makeSite(objectmap):
    from ..interfaces import IFolder
    from zope.interface import alsoProvides
    site = testing.DummyResource()
    alsoProvides(site, IFolder)
    services = testing.DummyResource()
    site['__services__'] = services
    services['objectmap'] = objectmap
    return site
