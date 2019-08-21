#  Copyright (c) 2018 SONATA-NFV, 5GTANGO, Paderborn University
# ALL RIGHTS RESERVED.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Neither the name of the SONATA-NFV, 5GTANGO, Paderborn University
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.sonata-nfv.eu).
#
# This work has also been performed in the framework of the 5GTANGO project,
# funded by the European Commission under Grant number 761493 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.5gtango.eu).
import os
from tngsdk.benchmark.helper import ensure_dir
from tngsdk.benchmark.logger import TangoLogger
from tngsdk.benchmark.ietf.vnf_bd import vnf_bd as VNF_BD_Model
import pyangbind.lib.pybindJSON as pybindJSON


LOG = TangoLogger.getLogger(__name__)


class IetfBmwgVnfBD_Generator(object):

    def __init__(self, args, service_experiments):
        self.args = args
        # check inputs and possibly skip
        if self.args.ibbd_dir is None:
            return
        self.service_experiments = service_experiments

    def run(self):
        # check inputs and possibly skip
        if self.args.ibbd_dir is None:
            LOG.info("IETF BMWG BD dir not specified (--ibbd). Skipping.")
            return
        # generate IETF BMWG BD, PP, BR
        for ex_id, ex in enumerate(self.service_experiments):
            # iterate over all experiment configurations
            for _, ec in enumerate(ex.experiment_configurations):
                # generate assets
                try:
                    bd_path = self._generate_bd(ex_id, ec)
                    LOG.debug("Generated IETF BMWG BD: {}".format(bd_path))
                except BaseException as exx:
                    LOG.error("Could not generate IETF VNF BD for EC: {}\n{}"
                              .format(ec, exx))

    def _generate_bd(self, ex_id, ec):
        # instantiate model
        m = VNF_BD_Model()
        # output path for YAML file
        bd_path = os.path.join(self.args.ibbd_dir,
                               "{}-bd.yaml".format(ec.name))
        # populate the model with the actual data
        # (always assing strings, assigning ints does not work,
        # types seem to be automaticall converted by the model)
        # 1. header section
        m.vnf_bd.id = "{:05d}".format(ec.run_id)
        m.vnf_bd.name = ec.name
        m.vnf_bd.version = "0.1"
        m.vnf_bd.author = "tng-bench"
        m.vnf_bd.description = ("BD generated by"
                                + " tng-bench (https://sndzoo.github.io/).")
        # 2. experiments section
        m.vnf_bd.experiments.methods = str(ex_id)
        m.vnf_bd.experiments.tests = str(
            ec.parameter.get("ep::header::all::config_id", -1))
        m.vnf_bd.experiments.trials = str(
            ec.parameter.get("ep::header::all::repetition", -1))
        # 3. environment section
        m.vnf_bd.environment.name = self.args.config.get(
            "targets")[0].get("name")
        m.vnf_bd.environment.description = self.args.config.get(
            "targets")[0].get("description")
        m.vnf_bd.environment.plugin.type = self.args.config.get(
            "targets")[0].get("pdriver")
        p1 = m.vnf_bd.environment.plugin.parameters.add("entrypoint")
        p1.value = self.args.config.get(
            "targets")[0].get("pdriver_config").get("host")
        # 4. targets section
        t1 = m.vnf_bd.targets.add("01")
        t1.author = ec.experiment.target.get("vendor")
        t1.name = ec.experiment.target.get("name")
        t1.version = ec.experiment.target.get("version")
        # 5. scenario section
        # TODO this must be build using the NS model and the CS.
        # (the generated VNFBDs would actually be of help here)
        n1 = m.vnf_bd.scenario.nodes.add("01")
        print(n1)
        l1 = m.vnf_bd.scenario.links.add("01")
        print(l1)
        # 6. proceedings section
        # TODO
        at1 = m.vnf_bd.proceedings.attributes.add("01")
        print(at1)
        ag1 = m.vnf_bd.proceedings.agents.add("01")
        print(ag1)
        mo1 = m.vnf_bd.proceedings.monitors.add("01")
        print(mo1)
        """
        # collect inputs for BD -> old version based on templates
        bd_in = dict()
        # BD information
        bd_in["bd_id"] = "{:05d}".format(ec.run_id)
        bd_in["bd_name"] = ec.name
        bd_in["bd_version"] = "0.1"
        bd_in["bd_author"] = "tng-bench"
        bd_in["bd_description"] = "BD generated by 5GTANGO benchmarking tool."
        # SUT information
        bd_in["sut_id"] = "sut01"  # fixed
        bd_in["sut_vendor"] = ec.experiment.target.get("vendor")
        bd_in["sut_name"] = ec.experiment.target.get("name")
        bd_in["sut_version"] = ec.experiment.target.get("version")
        bd_in["sut_author"] = bd_in["sut_vendor"]
        bd_in["sut_description"] = ec.experiment.description
        bd_in["sut_type"] = "5gtango"  # 5GTANGO SUTs only
        bd_in["sut_5gtango_pkgpath"] = ec.experiment.sut_package
        # SUT connections (TODO MP order matters, bad design)
        bd_in["sut_input_port_id"] = (ec.experiment.measurement_points[1]
                                      .get("connection_point"))
        bd_in["sut_input_port_type"] = "external"
        bd_in["sut_input_port_address"] = None
        bd_in["sut_output_port_id"] = (ec.experiment.measurement_points[0]
                                       .get("connection_point"))
        bd_in["sut_output_port_type"] = "external"
        bd_in["sut_output_port_address"] = None
        # Agent information (TODO MP order matters, bad design)
        bd_in["agent_1_id"] = ec.experiment.measurement_points[1].get("name")
        bd_in["agent_1_image"] = (ec.experiment.measurement_points[1]
                                  .get("container"))
        bd_in["agent_1_cp_id"] = "data"
        bd_in["agent_1_cp_address"] = (ec.experiment.measurement_points[1]
                                       .get("address"))
        bd_in["agent_2_id"] = ec.experiment.measurement_points[0].get("name")
        bd_in["agent_2_image"] = (ec.experiment.measurement_points[0]
                                  .get("container"))
        bd_in["agent_2_cp_id"] = "data"
        bd_in["agent_2_cp_address"] = (ec.experiment.measurement_points[0]
                                       .get("address"))
        # Links (TODO MP order matters, bad design)
        bd_in["network_type"] = "E-LINE"
        # Resource limits (TODO RL order matters, bad design)
        sut_func_name = ec.experiment.experiment_parameters[0].get("function")
        bd_in["sut_resource_cpu_cores"] = self._get_ep_from_ec(
            ec, sut_func_name, "cpu_cores")
        bd_in["sut_resource_cpu_bw"] = self._get_ep_from_ec(
            ec, sut_func_name, "cpu_bw")
        bd_in["sut_resource_mem"] = self._get_ep_from_ec(
            ec, sut_func_name, "mem_max")
        bd_in["agent_1_resource_cpu_cores"] = self._get_ep_from_ec(
            ec, bd_in["agent_1_id"], "cpu_cores")
        bd_in["agent_1_resource_cpu_bw"] = self._get_ep_from_ec(
            ec, bd_in["agent_1_id"], "cpu_bw")
        bd_in["agent_1_resource_mem"] = self._get_ep_from_ec(
            ec, bd_in["agent_1_id"], "mem_max")
        bd_in["agent_2_resource_cpu_cores"] = self._get_ep_from_ec(
            ec, bd_in["agent_2_id"], "cpu_cores")
        bd_in["agent_2_resource_cpu_bw"] = self._get_ep_from_ec(
            ec, bd_in["agent_2_id"], "cpu_bw")
        bd_in["agent_2_resource_mem"] = self._get_ep_from_ec(
            ec, bd_in["agent_2_id"], "mem_max")
        """
        # render BD using template
        bd_str = pybindJSON.dumps(m)  # self._render(bd_in, BD_TEMPLATE)
        print(bd_str)
        print("---")
        print((ec.parameter))
        print("---")
        print((ec.experiment.target))
        print("----")
        print(self.args.config)
        # write BD
        ensure_dir(bd_path)
        with open(bd_path, "w") as f:
            f.write(bd_str)
        return bd_path

    def _get_ep_from_ec(self, ec, node, ep_name):
        """
        Helper that get resource limit from flat
        parameter list of an EC.
        """
        for k in ec.parameter.keys():
            # fuzzy matchin using "in" statement
            if node in k and ep_name in k:
                return ec.parameter.get(k)
        LOG.warning("Could not find resource limit for node: {}"
                    .format(node))
        return None
