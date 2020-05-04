import axios from "axios";
import {ITelescopeStatus} from "../components/TelescopeStatus";

const API_ADDRESS = "http://10.1.1.19:8080";

export const api = {
    start: async () => {
        axios.post(`${API_ADDRESS}/start`).then(result => {
            console.log(result);
            return result;
        }).catch((err => {
            console.warn(err);
            throw err;
        }));
    },
    status: async () => {
        try {
            let result = await axios.get(`${API_ADDRESS}/status`);
            return result.data;
        } catch (ex) {
            throw ex;
        }
    },

};
