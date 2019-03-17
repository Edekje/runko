#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
namespace py = pybind11;

#include "../ffe/tile.h"


namespace ffe {

//--------------------------------------------------
template<size_t D>
auto declare_tile(
    py::module& m,
    const std::string& pyclass_name) 
{

  return 
  py::class_<ffe::Tile<D>, 
             fields::Tile<D>,
             std::shared_ptr<ffe::Tile<D>>
             >(m, pyclass_name.c_str())
    .def(py::init<size_t, size_t, size_t>())
    .def_readwrite("dx",        &ffe::Tile<D>::dx)
    .def_readwrite("cfl",       &ffe::Tile<D>::cfl)
    .def("compute_perp_current",    &ffe::Tile<D>::compute_perp_current)
    .def("subtract_parallel_e",     &ffe::Tile<D>::subtract_parallel_e);
}

//--------------------------------------------------

// python bindings for plasma classes & functions
void bind_ffe(py::module& m_sub)
{
  //--------------------------------------------------
  // 1D bindings
  //py::module m_1d = m_sub.def_submodule("oneD", "1D specializations");

  //--------------------------------------------------
  // 2D bindings
  py::module m_2d = m_sub.def_submodule("twoD", "2D specializations");
  auto t2 = ffe::declare_tile<2>(m_2d, "Tile");


  //--------------------------------------------------
  // 3D bindings
  //py::module m_3d = m_sub.def_submodule("threeD", "3D specializations");
  //auto t3 = ffe::declare_tile<3>(m_2d, "Tile");


}

} // end of ns ffe
