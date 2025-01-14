# -*- coding: utf-8 -*-
import heapq
from euclid3 import LineSegment2,Line2,operator,Ray2,Point2
from itertools import islice,tee, cycle, chain
from collections import namedtuple



def memoria(valor1,valor2,id,conta,donde):
	import psutil
	import os
	import time
	process = psutil.Process(os.getpid())
	mem = process.memory_info().rss / float(2 ** 20)
	if mem > valor2:
		print("La memoria del proceso supera 1GB y sera destruido")
		process.kill()
		time.sleep(3)
	return conta+1

def miLog(**dat):
	print(dat)

def _window(lst):
	prevs, items, nexts = tee(lst, 3)
	prevs = islice(cycle(prevs), len(lst) - 1, None)
	nexts = islice(cycle(nexts), 1, None)
	return zip(prevs, items, nexts)


def _cross(a, b):
	res = a.x * b.y - b.x * a.y
	return res


def _approximately_equals(a, b):
	from basico import data as d
	return a == b or (abs(a - b) <= max(abs(a), abs(b)) * d['APROX'])


def _approximately_same(point_a, point_b):
	return _approximately_equals(point_a.x, point_b.x) and _approximately_equals(point_a.y, point_b.y)


def _normalize_contour(contour):
	contour = [Point2(float(x), float(y)) for (x, y) in contour]
	return [point for prev, point, next in _window(contour) if not (point == next or (point-prev).normalized() == (next - point).normalized())]


class _SplitEvent(namedtuple("_SplitEvent", "distance, intersection_point, vertex, opposite_edge")):
	__slots__ = ()

	def __lt__(self, other):
		return self.distance < other.distance

	def __str__(self):
		return "{} Split event @ {} from {} to {}".format(self.distance, self.intersection_point, self.vertex, self.opposite_edge)


class _EdgeEvent(namedtuple("_EdgeEvent", "distance intersection_point vertex_a vertex_b")):
	__slots__ = ()

	def __lt__(self, other):
		return self.distance < other.distance

	def __str__(self):
		return "{} Edge event @ {} between {} and {}".format(self.distance, self.intersection_point, self.vertex_a, self.vertex_b)


_OriginalEdge = namedtuple("_OriginalEdge", "edge bisector_left, bisector_right")

Subtree = namedtuple("Subtree", "source, height, sinks")


class _LAVertex:
	def __init__(self, point, edge_left, edge_right, direction_vectors=None):
		self.point = point
		self.edge_left = edge_left
		self.edge_right = edge_right
		self.prev = None
		self.next = None
		self.lav = None
		self._valid = True  

		

		creator_vectors = (edge_left.v.normalized() * -1, edge_right.v.normalized())
		if direction_vectors is None:
			direction_vectors = creator_vectors

		self._is_reflex = (_cross(*direction_vectors)) < 0
		self._bisector = Ray2(self.point, operator.add(*creator_vectors) * (-1 if self.is_reflex else 1))
	@property
	def bisector(self):
		return self._bisector

	@property
	def is_reflex(self):
		return self._is_reflex

	@property
	def original_edges(self):
		return self.lav._slav._original_edges

	def next_event(self):
		from __init__ import data as d
		events = []
		if self.is_reflex:
			for edge in self.original_edges:
				if edge.edge == self.edge_left or edge.edge == self.edge_right:
					continue

				leftdot = self.edge_left.v.normalized().dot(edge.edge.v.normalized())
				rightdot = self.edge_right.v.normalized().dot(edge.edge.v.normalized())
				selfedge = self.edge_left if leftdot < rightdot else self.edge_right
				otheredge = self.edge_left if leftdot > rightdot else self.edge_right

				i = Line2(selfedge).intersect(Line2(edge.edge))
				if i is not None and not _approximately_equals(i, self.point):
					linvec = (self.point - i).normalized()
					edvec = edge.edge.v.normalized()
					if linvec.dot(edvec) < 0:
						edvec = -edvec

					bisecvec = edvec + linvec
					if abs(bisecvec) == 0:
						continue
					bisector = Line2(i, bisecvec)
					b = bisector.intersect(self.bisector)

					if b is None:
						continue

					xleft	= _cross(edge.bisector_left.v.normalized(), (b - edge.bisector_left.p).normalized()) > -d['EPSILON']
					xright	= _cross(edge.bisector_right.v.normalized(), (b - edge.bisector_right.p).normalized()) < d['EPSILON']
					xedge	= _cross(edge.edge.v.normalized(), (b - edge.edge.p).normalized()) < d['EPSILON']

					if not (xleft and xright and xedge):
						continue
					events.append(_SplitEvent(Line2(edge.edge).distance(b), b, self, edge.edge))

		i_prev = self.bisector.intersect(self.prev.bisector)
		i_next = self.bisector.intersect(self.next.bisector)

		if i_prev is not None:
			events.append(_EdgeEvent(Line2(self.edge_left).distance(i_prev), i_prev, self.prev, self))
		if i_next is not None:
			events.append(_EdgeEvent(Line2(self.edge_right).distance(i_next), i_next, self, self.next))

		if not events:
			return None

		ev = min(events, key=lambda event: self.point.distance(event.intersection_point))
		return ev

	def invalidate(self):
		if self.lav is not None:
			self.lav.invalidate(self)
		else:
			self._valid = False

	@property
	def is_valid(self):
		return self._valid

	def __str__(self):
		return "Vertex ({:.9f};{:.9f})".format(self.point.x, self.point.y)

	def __repr__(self):
		return "Vertex ({}) ({:.9f};{:.9f}), bisector {}, edges {} {}".format("reflex" if self.is_reflex else "convex",
																			  self.point.x, self.point.y, self.bisector,
																			  self.edge_left, self.edge_right)


class _SLAV:
	def __init__(self, polygon, holes):
		contours = [_normalize_contour(polygon)]
		contours.extend([_normalize_contour(hole) for hole in holes])

		self._lavs = [_LAV.from_polygon(contour, self) for contour in contours]
		self._original_edges = [
			_OriginalEdge(LineSegment2(vertex.prev.point, vertex.point), vertex.prev.bisector, vertex.bisector)
			for vertex in chain.from_iterable(self._lavs)
		]

	def __iter__(self):
		for lav in self._lavs:
			yield lav

	def __len__(self):
		return len(self._lavs)

	def empty(self):
		return len(self._lavs) == 0

	def handle_edge_event(self, event):
		sinks = []
		events = []

		lav = event.vertex_a.lav
		if event.vertex_a.prev == event.vertex_b.next:
			self._lavs.remove(lav)
			for vertex in list(lav):
				sinks.append(vertex.point)
				vertex.invalidate()
		else:
			new_vertex = lav.unify(event.vertex_a, event.vertex_b, event.intersection_point)
			if lav.head in (event.vertex_a, event.vertex_b):
				lav.head = new_vertex
			sinks.extend((event.vertex_a.point, event.vertex_b.point))
			next_event = new_vertex.next_event()
			if next_event is not None:
				events.append(next_event)

		return (Subtree(event.intersection_point, event.distance, sinks), events)

	def handle_split_event(self, event, _id):
		from __init__ import data as d
		lav = event.vertex.lav

		sinks = [event.vertex.point]
		vertices = []
		x = None  # right vertex
		y = None  # left vertex
		contador=30
		norm = event.opposite_edge.v.normalized()
		for v in chain.from_iterable(self._lavs):
			if norm == v.edge_left.v.normalized() and event.opposite_edge.p == v.edge_left.p:
				x = v
				y = x.prev
			elif norm == v.edge_right.v.normalized() and event.opposite_edge.p == v.edge_right.p:
				y = v
				x = y.next
			#miLog(_norm=norm,_x=x)
			if x:
				xleft	= _cross(y.bisector.v.normalized(), (event.intersection_point - y.point).normalized()) >= -d['EPSILON']
				xright	= _cross(x.bisector.v.normalized(), (event.intersection_point - x.point).normalized()) <= d['EPSILON']
				#miLog(_norm=norm,_xleft=xleft,_xright=xright)
				
			
				if xleft and xright:
					break
				else:
					x = None
					y = None
			else:            
				contador = memoria(100,1000,_id,contador,"FUNC Split")

		if x is None:
			return (None, [])

		v1 = _LAVertex(event.intersection_point, event.vertex.edge_left, event.opposite_edge)
		v2 = _LAVertex(event.intersection_point, event.opposite_edge, event.vertex.edge_right)
		#miLog(LAV=lav,_v1=v1,_v2=v2)
		
		

		v1.prev = event.vertex.prev
		v1.next = x
		event.vertex.prev.next = v1
		x.prev = v1

		v2.prev = y
		v2.next = event.vertex.next
		event.vertex.next.prev = v2
		y.next = v2

	

		new_lavs = None
		self._lavs.remove(lav)
		if lav != x.lav:
			try: 
				self._lavs.remove(x.lav)
			except:
				return (None, [])
			new_lavs = [_LAV.from_chain(v1, self)]
		else:
			new_lavs = [_LAV.from_chain(v1, self), _LAV.from_chain(v2, self)]

		for l in new_lavs:
			if len(l) > 2:
				self._lavs.append(l)
				vertices.append(l.head)
			else:
				sinks.append(l.head.next.point)
				for v in list(l):
					v.invalidate()

		events = []
		for vertex in vertices:
			next_event = vertex.next_event()
			if next_event is not None:
				events.append(next_event)
		event.vertex.invalidate()
		return (Subtree(event.intersection_point, event.distance, sinks), events)


class _LAV:
	def __init__(self, slav):
		self.head = None
		self._slav = slav
		self._len = 0

	@classmethod
	def from_polygon(cls, polygon, slav):
		lav = cls(slav)
		for prev, point, next in _window(polygon):
			lav._len += 1
			vertex = _LAVertex(point, LineSegment2(prev, point), LineSegment2(point, next))
			vertex.lav = lav
			if lav.head is None:
				lav.head = vertex
				vertex.prev = vertex.next = vertex
			else:
				vertex.next = lav.head
				vertex.prev = lav.head.prev
				vertex.prev.next = vertex
				lav.head.prev = vertex
		return lav

	@classmethod
	def from_chain(cls, head, slav):
		lav = cls(slav)
		lav.head = head
		for vertex in lav:
			lav._len += 1
			vertex.lav = lav
		return lav

	def invalidate(self, vertex):
		assert vertex.lav is self, "Tried to invalidate a vertex that's not mine"
		vertex._valid = False
		if self.head == vertex:
			self.head = self.head.next
		vertex.lav = None

	def unify(self, vertex_a, vertex_b, point):
		replacement = _LAVertex(point, vertex_a.edge_left, vertex_b.edge_right,
								(vertex_b.bisector.v.normalized(), vertex_a.bisector.v.normalized()))
		replacement.lav = self

		if self.head in [vertex_a, vertex_b]:
			self.head = replacement

		vertex_a.prev.next = replacement
		vertex_b.next.prev = replacement
		replacement.prev = vertex_a.prev
		replacement.next = vertex_b.next

		vertex_a.invalidate()
		vertex_b.invalidate()

		self._len -= 1
		return replacement

	def __str__(self):
		return "LAV {}".format(id(self))

	def __repr__(self):
		return "{} = {}".format(str(self), [vertex for vertex in self])

	def __len__(self):
		return self._len

	def __iter__(self):
		cur = self.head
		while True:
			yield cur
			cur = cur.next
			if cur == self.head:
				return

	def _show(self):
		cur = self.head
		while True:
			print(cur.__repr__())
			cur = cur.next
			if cur == self.head:
				break


class _EventQueue:
	def __init__(self):
		self.__data = []

	def put(self, item):
		if item is not None:
			heapq.heappush(self.__data, item)

	def put_all(self, iterable):
		for item in iterable:
			heapq.heappush(self.__data, item)

	def get(self):
		return heapq.heappop(self.__data)

	def empty(self):
		return len(self.__data) == 0

	def peek(self):
		return self.__data[0]

	def show(self):
		for item in self.__data:
			print(item)
            

	
def skeletonize(polygon,id=0,holes=[]):
	from . import  data as d
	slav = _SLAV(polygon, holes)
	output = {"lin":[],"cen":[]}
	prioque = _EventQueue()
	for lav in slav:
		for vertex in lav:
			prioque.put(vertex.next_event())

	while not (prioque.empty() or slav.empty()):
		i = prioque.get()
		if isinstance(i, _EdgeEvent):
			if not i.vertex_a.is_valid or not i.vertex_b.is_valid:
				continue
			(arc, events) = slav.handle_edge_event()
		elif isinstance(i, _SplitEvent):
			continue
		(arc, events) = slav.handle_split_event(i,id)

		prioque.put_all(events)
		if arc is not None:
			contNones = 0
			for sink in arc.sinks:
				if (arc.source.x, arc.source.y) in polygon or (sink.x, sink.y) in polygon:
					output["lin"].append([(arc.source.x, arc.source.y),(sink.x, sink.y)])
				else:
					output["cen"].append((arc.source.x, arc.source.y))
					output["cen"].append((sink.x, sink.y))
		else:
			contNones += 1
			if contNones > 3:
				break
	return output


