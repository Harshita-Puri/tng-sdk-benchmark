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
import yaml
from tngsdk.benchmark.helper import ensure_dir, download_file
from jinja2 import Environment, FileSystemLoader
from tngsdk.benchmark.logger import TangoLogger


LOG = TangoLogger.getLogger(__name__)


# where to fetch the latest tempaltes:
BD_TEMPLATE_URL = ("https://raw.githubusercontent.com/mpeuster/"
                   + "vnf-bench-model/dev/vnf-br/templates/"
                   + "vnf-bd.yaml")
# BD_TEMPLATE_URL = "file://{}".format(os.path.abspath(
#    "../vnf-bench-model/vnf-br/templates/vnf-bd.yaml"))
# local template storage
TEMPLATE_PATH = "/tmp/tng-bench/templates"
BD_TEMPLATE = "vnf-bd.yaml"


class IetfBmwgResultProcessor(object):

    def __init__(self, args, service_experiments):
        self.args = args
        if self.args.ibbd_dir is None:
            LOG.info("IETF BMWG BD dir not specified (--ibbd). Skipping.")
            return
        self.service_experiments = service_experiments
        # fetch BD template from GitHub
        if not download_file(BD_TEMPLATE_URL,
                             os.path.join(
                                TEMPLATE_PATH, BD_TEMPLATE)):
            # TODO this is temporary, don't rely on online resources
            raise BaseException("Could not download BD template. Abort.")
        # instantiate reder environment
        self.render_env = Environment(
            loader=FileSystemLoader(TEMPLATE_PATH),
            trim_blocks=True,
            lstrip_blocks=True)

    def run(self):
        # check inputs and possibly skip
        if self.args.ibbd_dir is None:
            return
        # generate IETF BMWG BD, PP, BR
        for ex in self.service_experiments:
            # iterate over all experiment configurations
            for ec in ex.experiment_configurations:
                # generate assets
                bd = self._generate_bd(ec)
                pp = self._generate_pp(ec)
                self._generate_br(ec, bd, pp)

    def _generate_bd(self, ec):
        # output path for YAML file
        bd_path = os.path.join(self.args.ibbd_dir,
                               "{}-bd.yaml".format(ec.name))

        # collect inputs for BD
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

        # render BD using template
        bd_str = self._render(bd_in, BD_TEMPLATE)
        # write BD
        ensure_dir(bd_path)
        with open(bd_path, "w") as f:
            f.write(bd_str)
        LOG.debug("Generated IETF BMWG BD: {}".format(bd_path))
        # parse YAML string and return redered dict
        return yaml.load(bd_str)

    def _generate_pp(self, ec):
        return dict()

    def _generate_br(self, ec, bd, pp):
        pass

    def _render(self, data, template):
        t = self.render_env.get_template(template)
        return t.render(data)

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
